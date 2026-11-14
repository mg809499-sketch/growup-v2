from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from app.core.errors import AppError
from app.domains.content.blocks import PageLayout
from app.domains.content.models import Page, PageStatus, PageVersion
from app.domains.content.service import PageService


class FakePageRepository:
    def __init__(self) -> None:
        self.published: list[dict[str, object]] = []
        self.created: list[dict[str, object]] = []
        self.version = PageVersion(
            id=uuid4(),
            tenant_id=uuid4(),
            page_id=uuid4(),
            version=3,
            layout={"version": 3, "blocks": []},
            created_by=None,
            created_at=datetime.now(UTC),
        )
        self.latest: PageVersion | None = self.version
        self.page = Page(
            id=self.version.page_id,
            tenant_id=self.version.tenant_id,
            slug="home",
            title="Inicio",
            status=PageStatus.DRAFT,
            published_version_id=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

    async def get_page(self, tenant_id: UUID, page_id: UUID) -> Page | None:
        return self.page if page_id == self.page.id else None

    async def get_version(
        self, tenant_id: UUID, page_id: UUID, version_id: UUID
    ) -> PageVersion | None:
        return self.version if version_id == self.version.id else None

    async def latest_version(self, tenant_id: UUID, page_id: UUID) -> PageVersion | None:
        return self.latest

    async def create_version(
        self,
        tenant_id: UUID,
        *,
        page_id: UUID,
        layout: dict[str, object],
        created_by: UUID | None,
    ) -> PageVersion:
        self.created.append(
            {"page_id": page_id, "layout": layout, "created_by": created_by}
        )
        new_version = PageVersion(
            id=uuid4(),
            tenant_id=self.version.tenant_id,
            page_id=page_id,
            version=(self.latest.version + 1) if self.latest else 1,
            layout=layout,
            created_by=created_by,
            created_at=datetime.now(UTC),
        )
        self.version = new_version
        self.latest = new_version
        return new_version

    async def publish(
        self, tenant_id: UUID, *, page_id: UUID, version_id: UUID, actor_id: UUID
    ) -> None:
        self.published.append(
            {"page_id": page_id, "version_id": version_id, "actor_id": actor_id}
        )


@pytest.mark.asyncio
async def test_publish_requires_expected_version() -> None:
    repository = FakePageRepository()
    service = PageService(repository)  # type: ignore[arg-type]
    actor = uuid4()

    with pytest.raises(AppError) as excinfo:
        await service.publish(
            repository.version.tenant_id,
            repository.version.page_id,
            version_id=repository.version.id,
            expected_version=1,
            actor_id=actor,
        )

    assert excinfo.value.code == "VERSION_CONFLICT"
    assert excinfo.value.status_code == 409
    assert repository.published == []


@pytest.mark.asyncio
async def test_publish_swaps_atomically() -> None:
    repository = FakePageRepository()
    service = PageService(repository)  # type: ignore[arg-type]
    actor = uuid4()

    await service.publish(
        repository.version.tenant_id,
        repository.version.page_id,
        version_id=repository.version.id,
        expected_version=3,
        actor_id=actor,
    )

    assert repository.published == [
        {
            "page_id": repository.version.page_id,
            "version_id": repository.version.id,
            "actor_id": actor,
        }
    ]


def test_preview_token_roundtrip() -> None:
    tenant_id, page_id, version_id = uuid4(), uuid4(), uuid4()
    token = PageService.sign_preview_token(tenant_id, page_id, version_id, ttl_seconds=60)
    assert PageService.verify_preview_token(token) == (tenant_id, page_id, version_id)


def test_preview_token_rejects_tampering() -> None:
    tenant_id, page_id, version_id = uuid4(), uuid4(), uuid4()
    token = PageService.sign_preview_token(tenant_id, page_id, version_id, ttl_seconds=60)
    tampered = token[:-2] + ("00" if not token.endswith("00") else "ff")
    with pytest.raises(AppError) as excinfo:
        PageService.verify_preview_token(tampered)
    assert excinfo.value.code == "PREVIEW_INVALID"


def test_preview_token_rejects_wrong_shape() -> None:
    with pytest.raises(AppError):
        PageService.verify_preview_token("not-a-token")

def _layout() -> PageLayout:
    return PageLayout(
        version=1,
        blocks=[{"id": "hero-1", "type": "hero", "title": "Hola"}],
    )


async def test_create_draft_without_expected_version_allows_save() -> None:
    repository = FakePageRepository()
    service = PageService(repository)  # type: ignore[arg-type]
    version = await service.create_draft(
        repository.version.tenant_id,
        repository.version.page_id,
        layout=_layout(),
        actor_id=None,
    )
    assert version.version == 4
    assert repository.created


async def test_create_draft_expected_matching_version_allows_save() -> None:
    repository = FakePageRepository()
    service = PageService(repository)  # type: ignore[arg-type]
    version = await service.create_draft(
        repository.version.tenant_id,
        repository.version.page_id,
        layout=_layout(),
        actor_id=None,
        expected_version=3,
    )
    assert version.version == 4


async def test_create_draft_expected_zero_allowed_when_empty() -> None:
    repository = FakePageRepository()
    repository.latest = None
    service = PageService(repository)  # type: ignore[arg-type]
    version = await service.create_draft(
        repository.version.tenant_id,
        repository.version.page_id,
        layout=_layout(),
        actor_id=None,
        expected_version=0,
    )
    assert version.version == 1


async def test_create_draft_expected_zero_rejected_when_draft_exists() -> None:
    repository = FakePageRepository()
    service = PageService(repository)  # type: ignore[arg-type]
    with pytest.raises(AppError) as excinfo:
        await service.create_draft(
            repository.version.tenant_id,
            repository.version.page_id,
            layout=_layout(),
            actor_id=None,
            expected_version=0,
        )
    assert excinfo.value.code == "VERSION_CONFLICT"
    assert excinfo.value.status_code == 409
    assert excinfo.value.details["expected"] == 0
    assert excinfo.value.details["latest"] == 3
    assert repository.created == []


async def test_create_draft_expected_mismatch_conflicts() -> None:
    repository = FakePageRepository()
    service = PageService(repository)  # type: ignore[arg-type]
    with pytest.raises(AppError) as excinfo:
        await service.create_draft(
            repository.version.tenant_id,
            repository.version.page_id,
            layout=_layout(),
            actor_id=None,
            expected_version=7,
        )
    assert excinfo.value.code == "VERSION_CONFLICT"
    assert excinfo.value.status_code == 409
    assert excinfo.value.details == {"expected": 7, "latest": 3}
    assert repository.created == []


async def test_create_draft_concurrent_editor_loses_write() -> None:
    """Dos editores parten de la v3; el que guarda primero crea v4; el segundo, 409."""
    repository = FakePageRepository()
    service = PageService(repository)  # type: ignore[arg-type]
    first = await service.create_draft(
        repository.version.tenant_id,
        repository.version.page_id,
        layout=_layout(),
        actor_id=None,
        expected_version=3,
    )
    assert first.version == 4
    with pytest.raises(AppError) as excinfo:
        await service.create_draft(
            repository.version.tenant_id,
            repository.version.page_id,
            layout=_layout(),
            actor_id=None,
            expected_version=3,
        )
    assert excinfo.value.code == "VERSION_CONFLICT"
    assert excinfo.value.details["latest"] == 4

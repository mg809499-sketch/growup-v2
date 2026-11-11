from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.domains.content.blocks import (
    FaqBlock,
    HeaderBlock,
    HeroBlock,
    PageLayout,
    RichTextBlock,
    VideoEmbedBlock,
)


def _base() -> dict[str, object]:
    return {"id": "b1"}


def test_hero_block_valid() -> None:
    block = HeroBlock(**_base(), title="Nueva colección")
    assert block.align == "left"


def test_rich_text_rejects_html() -> None:
    with pytest.raises(ValidationError):
        RichTextBlock(**_base(), markdown="Hola <script>alert(1)</script>")


def test_rich_text_markdown_ok() -> None:
    block = RichTextBlock(**_base(), markdown="Envíos **gratis** en Bogotá")
    assert "gratis" in block.markdown


def test_video_embed_allowlist() -> None:
    with pytest.raises(ValidationError):
        VideoEmbedBlock(**_base(), url="https://evil.example.com/video")
    ok = VideoEmbedBlock(**_base(), url="https://www.youtube.com/watch?v=abc123")
    assert "youtube" in ok.url


def test_faq_max_items() -> None:
    items = [{"question": f"q{i}", "answer": f"a{i}"} for i in range(13)]
    with pytest.raises(ValidationError):
        FaqBlock(**_base(), items=items)


def test_header_rejects_extra_props() -> None:
    with pytest.raises(ValidationError):
        HeaderBlock(**_base(), nav=[], onclick="alert(1)")  # type: ignore[call-arg]


def test_image_requires_alt() -> None:
    with pytest.raises(ValidationError):
        HeroBlock(**_base(), title="x", image={"url": "https://cdn.growup.com/a.jpg", "alt": ""})  # type: ignore[arg-type]


def test_page_layout_roundtrip_discriminated() -> None:
    layout = PageLayout(
        version=1,
        blocks=[  # type: ignore[list-item]
            {"type": "hero", "id": "h1", "title": "Hola", "align": "center"},
            {
                "type": "spacer",
                "id": "s1",
                "height": "md",
            },
        ],
    )
    dumped = layout.model_dump(mode="json")
    restored = PageLayout.model_validate(dumped)
    assert restored.blocks[0].type == "hero"  # type: ignore[union-attr]


def test_page_layout_rejects_unknown_block() -> None:
    with pytest.raises(ValidationError):
        PageLayout(
            version=1,
            blocks=[{"type": "iframe", "id": "x1"}],  # type: ignore[list-item]
        )


def test_columns_block_nested() -> None:
    layout = PageLayout(
        version=1,
        blocks=[  # type: ignore[list-item]
            {
                "type": "columns",
                "id": "c1",
                "columns": [
                    {
                        "width": 6,
                        "blocks": [
                            {"type": "rich_text", "id": "rt1", "markdown": "izq"},
                        ],
                    },
                    {
                        "width": 6,
                        "blocks": [{"type": "spacer", "id": "sp1", "height": "sm"}],
                    },
                ],
            }
        ],
    )
    assert layout.blocks[0].type == "columns"  # type: ignore[union-attr]


def test_too_many_blocks_rejected() -> None:
    blocks = [{"type": "spacer", "id": f"s{i}", "height": "sm"} for i in range(257)]
    with pytest.raises(ValidationError):
        PageLayout(version=1, blocks=blocks)  # type: ignore[arg-type]

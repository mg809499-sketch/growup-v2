from app.domains.content.blocks import PageLayout
from app.domains.content.templates import list_templates, load_template


def test_list_templates_returns_json_validated():
    items = list_templates()
    assert items, "templates directory empty"
    for item in items:
        assert item.template_id
        assert item.name
        assert item.description is not None


def test_ropa_starter_template_loads():
    layout = load_template("ropa-starter")
    assert isinstance(layout, PageLayout)
    assert layout.blocks


def test_joyeria_starter_template_loads():
    layout = load_template("joyeria-starter")
    assert isinstance(layout, PageLayout)
    assert layout.blocks
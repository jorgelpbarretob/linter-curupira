from ste_lint.catalog import RULE_CATALOG, build_registry


def test_phase3_catalog_is_explicit_empty_and_startup_valid() -> None:
    registry = build_registry()

    registry.validate_startup()
    assert RULE_CATALOG == ()
    assert registry.all() == ()

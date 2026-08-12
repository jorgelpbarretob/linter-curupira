from ste_lint.catalog import RULE_CATALOG, build_registry


def test_catalog_contains_the_seven_reviewed_previews() -> None:
    registry = build_registry()

    registry.validate_startup()
    assert [metadata.rule_id for metadata in RULE_CATALOG] == [
        "STE-I9-PUNCT-001",
        "STE-I9-SENT-001",
        "STE-I9-SENT-002",
        "STE-I9-PARA-001",
        "STE-I9-LIST-001",
        "STE-I9-VOICE-001",
        "STE-I9-NOTE-001",
    ]
    assert [rule.metadata.rule_id for rule in registry.all()] == [
        "STE-I9-LIST-001",
        "STE-I9-NOTE-001",
        "STE-I9-PARA-001",
        "STE-I9-PUNCT-001",
        "STE-I9-SENT-001",
        "STE-I9-SENT-002",
        "STE-I9-VOICE-001",
    ]

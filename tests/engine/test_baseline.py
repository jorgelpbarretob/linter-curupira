import json

import pytest

from ste_lint.domain import (
    Diagnostic,
    Document,
    RuleId,
    Severity,
    SourceLocation,
    SourceReference,
)
from ste_lint.engine import (
    Baseline,
    BaselineError,
    apply_baseline,
    build_baseline,
    parse_baseline,
    serialize_baseline,
)


def diagnostic(document: Document, start: int) -> Diagnostic:
    return Diagnostic(
        rule_id=RuleId("PROJECT-TEST-001"),
        source=SourceReference(standard="PROJECT", issue="1", locator="local-test"),
        severity=Severity.WARNING,
        location=SourceLocation(
            uri=document.uri,
            start_offset=start,
            end_offset=start + 1,
            start_line=1,
            start_column=start + 1,
            end_line=1,
            end_column=start + 2,
        ),
        message="Synthetic message.",
        explanation="Synthetic explanation.",
    )


def test_baseline_survives_inserted_content_before_the_context_line() -> None:
    original = Document(uri="manual.txt", text="A; B.\n")
    original_diagnostic = diagnostic(original, 1)
    baseline = build_baseline(original, (original_diagnostic,))
    changed = Document(uri="manual.txt", text="New line.\nA; B.\n")
    changed_diagnostic = diagnostic(changed, changed.text.index(";"))

    remaining = apply_baseline(changed, (changed_diagnostic,), baseline)

    assert remaining == ()


def test_baseline_does_not_suppress_changed_context() -> None:
    original = Document(uri="manual.txt", text="A; B.\n")
    baseline = build_baseline(original, (diagnostic(original, 1),))
    changed = Document(uri="manual.txt", text="A; C.\n")

    remaining = apply_baseline(changed, (diagnostic(changed, 1),), baseline)

    assert len(remaining) == 1


def test_baseline_distinguishes_repeated_identical_findings_by_ordinal() -> None:
    document = Document(uri="manual.txt", text="A; B.\nA; B.\n")
    first = diagnostic(document, document.text.index(";"))
    second = diagnostic(document, document.text.rindex(";"))
    baseline = build_baseline(document, (first,))

    remaining = apply_baseline(document, (first, second), baseline)

    assert remaining == (second,)


def test_baseline_json_is_sorted_strict_and_contains_no_document_text() -> None:
    baseline = Baseline(("sha256:" + "b" * 64, "sha256:" + "a" * 64))

    serialized = serialize_baseline(baseline)

    assert serialized.endswith("\n")
    assert "Synthetic" not in serialized
    assert json.loads(serialized) == {
        "schema_version": "1.0",
        "fingerprints": ["sha256:" + "a" * 64, "sha256:" + "b" * 64],
    }
    assert parse_baseline(serialized) == Baseline(("sha256:" + "a" * 64, "sha256:" + "b" * 64))


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ('{"schema_version":"2.0","fingerprints":[]}', "schema_version"),
        ('{"schema_version":"1.0","fingerprints":[],"extra":1}', "unknown"),
        ('{"schema_version":"1.0","fingerprints":["bad"]}', "fingerprint"),
        (
            '{"schema_version":"1.0","fingerprints":["sha256:'
            + "a" * 64
            + '","sha256:'
            + "a" * 64
            + '"]}',
            "duplicate",
        ),
    ],
)
def test_baseline_rejects_invalid_contract(text: str, message: str) -> None:
    with pytest.raises(BaselineError, match=message):
        parse_baseline(text)

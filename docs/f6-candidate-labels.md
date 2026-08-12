# Phase 6 NLP candidates and seed labels

Status: Approved for fixtures
Date: 2026-08-12
Normative source: ASD-STE100 Simplified Technical English, Issue 9
Source: https://www.asd-ste100.org/assets/files/ASD-STE100_ISSUE9.pdf

All summaries and English examples below are short, synthetic and written for
this project. They are not copied from the standard. Both candidates are
`nlp`, partial automation, `preview/info`, and have no autofix.

## STE-I9-VOICE-001 — conservative passive voice

Locator: Part 1, Section 3, Rule 3.6.

Project paraphrase: report a confidently parsed passive construction in
procedural text; in descriptive text, report only when the construction
identifies an agent.

Controls and abstention:

- procedural text: report a parser-confirmed passive with an explicit agent or
  an unambiguous modal/auxiliary verbal chain; abstain for a bare
  `be + participle` construction that can describe a state;
- descriptive and procedural-note text: report only when the parse contains an
  explicit agent; agentless passive abstains because the exception depends on
  whether the agent is unknown;
- do not classify past participles used as adjectives as passive voice;
- require one complete, contiguous sentence and consistent dependency offsets;
- no suggestion because the correct agent or rewrite is not mechanically known.

Proposed seed labels use two independent axes. `Truth = indeterminate` means the
sentence alone cannot establish the normative exception; it is not a
non-violation. `Expected = abstain` is excluded from TP/FP/FN/TN.

| Truth | Expected | Text type | Synthetic sentence | Reason |
|---|---|---|---|---|
| violation | emit | procedural | `The access panel is removed by the technician.` | clear passive with agent |
| violation | emit | procedural | `The pressure must be adjusted before the test.` | modal passive predicate |
| violation | emit | descriptive | `The signal is processed by the control unit.` | descriptive passive with agent |
| non-violation | no-emit | procedural | `Remove the access panel.` | active imperative |
| non-violation | no-emit | descriptive | `The control unit processes the signal.` | active descriptive sentence |
| indeterminate | abstain | descriptive | `The data was corrupted during transmission.` | text does not establish whether the agent is unknown |
| non-violation | no-emit | descriptive | `The installed valve is blue.` | participle modifies a noun |
| non-violation | no-emit | procedural | `If the pressure is high, open the valve.` | copular condition plus active command |
| indeterminate | abstain | procedural-note | `The panel is installed in the bay.` | agentless note case cannot establish the exception |
| indeterminate | abstain | procedural | `The valve is closed.` | bare participle can describe a state or action |

## STE-I9-NOTE-001 — imperative in a declared note

Locator: Part 1, Section 5, Rule 5.5.

Project paraphrase: in text explicitly declared as a procedural note, report a
sentence confidently parsed as an imperative instruction.

Controls and abstention:

- run only for `text_type = "procedural-note"`;
- require a base-form command root without an explicit grammatical subject;
- support negative commands and a leading conditional clause;
- require one complete, contiguous sentence and consistent dependency offsets;
- abstain for fragments, infinitival phrases without an independent imperative
  root and other ambiguous roots; a purpose clause followed by a separate
  imperative root remains detectable;
- no suggestion because content can belong in a work step or require a rewrite.

Proposed seed labels:

| Truth | Expected | Text type | Synthetic sentence | Reason |
|---|---|---|---|---|
| violation | emit | procedural-note | `Remove the access cover.` | direct imperative |
| violation | emit | procedural-note | `Do not touch the hot surface.` | negative imperative |
| violation | emit | procedural-note | `If the indicator flashes, stop the test.` | conditional plus imperative root |
| non-violation | no-emit | procedural-note | `The access cover is open.` | descriptive statement |
| non-violation | no-emit | procedural-note | `You can use an equivalent tool.` | explicit subject and modal statement |
| non-violation | no-emit | procedural-note | `The indicator will become stable after ten seconds.` | descriptive future statement |
| violation | emit | procedural-note | `To remove the cover, use tool ZX-4.` | infinitival phrase plus imperative root |
| non-violation | no-emit | procedural-note | `Removal of the cover is not necessary.` | nominal statement |
| indeterminate | abstain | procedural-note | `Access cover removal.` | incomplete fragment |
| violation | emit | procedural-note | `See section 3 for dimensions.` | imperative reference still gives an instruction |

## Evaluation gate

The labels above satisfy only the minimum seed structure. TP/FP/FN/TN use only
determinate `violation` and `non-violation` truth. Indeterminate cases report
abstention separately: `indeterminate_abstention_rate` is indeterminate cases
without emission divided by all indeterminate cases. An emission on an
indeterminate case is an unsafe emission and must remain zero. For determinate
truth, any emission is the positive prediction and no emission is the negative
prediction; thus a missed violation remains FN and a quiet non-violation remains
TN. Implementation must add further synthetic technical cases, report the
confusion matrix, abstention rate, unsafe emissions and Wilson intervals, and
keep each rule `preview` unless precision is at least 0.95 with sufficient
evidence. The maintainer approved ADR-014, both candidates, their IDs and these
revised labels on 2026-08-12.

The executable corpus in `tests/corpus/data/f6_nlp_seed.json` preserves these
20 approved labels and adds six synthetic technical cases for the Phase 6
evaluation gate. No normative example or vocabulary entry is included.

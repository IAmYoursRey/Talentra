# Domain model reference

## Portfolio state machine
Recommended transitions:

```text
draft -> submitted
submitted -> approved
submitted -> revision_requested
submitted -> rejected
revision_requested -> submitted
```

Do not overwrite historical validation decisions.

## Validation invariant
A portfolio item contributes to published skill evidence only when the current accepted revision is `approved`.

## Skill evidence
A normalized skill signal should retain:
- student UUID
- evidence source type
- portfolio/revision UUID or rubric assessment UUID
- canonical skill/tag ID
- normalized contribution value
- validator/source provenance
- timestamp/semester
- scoring-rules version

## Recommended tag model
Do not allow free-form hashtags to become canonical scoring categories directly.
Use:
- canonical tag catalog (`web-development`, `public-speaking`, `leadership`)
- display labels/localization
- optional student-entered notes
- aliases mapped to canonical IDs

Submission requirement: exactly 3–5 canonical tags unless product policy is changed.

## Radar score
Keep the formula deterministic. A reasonable MVP model can combine:
- approved evidence tag contributions,
- teacher rubric observations,
- capped repetition bonus,
- optional recency weight.

Persist the scoring-rules version and show the user what contributed.

## Recommendation model
Prefer deterministic retrieval/ranking first:
1. aggregate validated skill signals,
2. map skill clusters to study/career profiles,
3. compute score/confidence,
4. choose top candidates according to transparent rules,
5. use an LLM only to explain grounded results in natural language.

This keeps the ranking testable and prevents generated prose from silently changing the decision logic.

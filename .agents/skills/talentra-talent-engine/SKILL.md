---
name: talentra-talent-engine
description: Build TALENTRA deterministic skill scoring, school heatmap aggregation, longitudinal study/career matching, and grounded industry-language translation.
---

# Talent engine procedure

## Deterministic first
1. Read eligible approved evidence.
2. Normalize canonical tag/rubric signals.
3. Apply versioned weights/caps/recency rules.
4. Produce skill vector with provenance.
5. Map skill vector to versioned study/career profiles.
6. Compute score/confidence deterministically.
7. Only then generate human-readable explanation.

## Required properties
- Same inputs + same rules version => same numeric result.
- Every output can list contributing signal categories.
- Protected traits are excluded.
- Pending/rejected evidence is excluded.
- Repetition should be capped so many near-duplicate uploads cannot dominate.
- School heatmaps use aggregates and minimum-group privacy threshold.

## Industry-language translator
Input must carry factual source text/evidence. Output may professionalize wording but must preserve facts. Add a factuality test set containing prompts that tempt the model to invent metrics, leadership, or tools; those additions must be rejected/omitted.

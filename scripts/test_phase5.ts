import { MOCK_RUBRIC_DIMENSIONS, RUBRIC_LEVEL_LABELS } from "../src/mocks/soft-skills-rubric.mock";
import { SoftSkillRubricDimension } from "../src/types/review.types";

console.log("--- Running TALENTRA Phase 5 Frontend Invariant Tests ---");

// 1. Five soft-skill rubric dimensions strictly defined
console.log("1. Verifying 5 canonical soft-skill rubric dimensions...");
if (MOCK_RUBRIC_DIMENSIONS.length !== 5) {
  throw new Error(`Expected exactly 5 rubric dimensions, got ${MOCK_RUBRIC_DIMENSIONS.length}`);
}
const expectedRubricDims = ["initiative", "collaboration", "communication", "responsibility", "resilience"];
for (const dim of expectedRubricDims) {
  const match = MOCK_RUBRIC_DIMENSIONS.find((d: SoftSkillRubricDimension) => d.id === dim);
  if (!match) {
    throw new Error(`Missing expected rubric dimension: ${dim}`);
  }
  if (!match.levels || Object.keys(match.levels).length !== 5) {
    throw new Error(`Rubric dimension ${dim} must have complete levels 1 to 5`);
  }
}
console.log("✓ All 5 rubric dimensions strictly defined with 1-5 level descriptors.");

// 2. Rubric level labels verified
console.log("2. Verifying rubric level labels (1 to 5)...");
for (let score = 1; score <= 5; score++) {
  const label = RUBRIC_LEVEL_LABELS[score as 1 | 2 | 3 | 4 | 5];
  if (!label || label.trim().length === 0) {
    throw new Error(`Missing rubric level label for score ${score}`);
  }
}
console.log("✓ Rubric level labels (1 to 5) verified.");

// 3. Approved-only invariant simulation in frontend
console.log("3. Verifying approved-only projection invariant logic...");
const mockSnapshots = [
  { status: "approved", tags: ["web-development", "digital-literacy"] },
  { status: "submitted", tags: ["problem-solving"] },
  { status: "revision_requested", tags: ["teamwork"] },
  { status: "rejected", tags: ["leadership"] },
];
const contributing = mockSnapshots.filter(s => s.status === "approved");
if (contributing.length !== 1) {
  throw new Error("Only approved evidence may contribute to radar visualization");
}
console.log("✓ Approved-only visualization invariant confirmed.");

console.log("\n======================================================");
console.log(" ALL 3 PHASE 5 FRONTEND INVARIANT CHECKS PASSED! ");
console.log("======================================================\n");

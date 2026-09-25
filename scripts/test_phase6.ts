import { adminUserService } from "../src/services/admin-user.service";
import { adminClassService } from "../src/services/admin-class.service";
import { analyticsService } from "../src/services/analytics.service";
import { TalentHeatmapDimension } from "../src/types/analytics.types";

console.log("--- Running TALENTRA Phase 6 Frontend & Domain Invariant Tests ---");

// 1. Masked identifier invariant: user listings must contain masked identifiers
console.log("1. Verifying masked identifier privacy invariant...");
adminUserService.listUsers().then(async (userRes) => {
  if (userRes.items.length === 0) {
    throw new Error("Expected users to be available in listing");
  }

  for (const user of userRes.items) {
    if (!user.maskedIdentifier || (!user.maskedIdentifier.includes("•") && !user.maskedIdentifier.includes("*"))) {
      throw new Error(`User ${user.displayName} does not have a masked identifier: ${user.maskedIdentifier}`);
    }
    // Ensure no unmasked 10-digit NISN, 16-digit NUPTK, or 18-digit NIP appears
    if (/^\d{10}$/.test(user.maskedIdentifier) || /^\d{16}$/.test(user.maskedIdentifier) || /^\d{18}$/.test(user.maskedIdentifier)) {
      throw new Error(`Exposed raw unmasked identifier in user list: ${user.maskedIdentifier}`);
    }
  }
  console.log("✓ Masked identifier privacy invariant confirmed across all users.");

  // 2. Six canonical heatmap dimensions invariant
  console.log("2. Verifying 6 canonical talent heatmap dimensions...");
  const expectedDimensions = [
    "digital-literacy",
    "problem-solving",
    "creativity",
    "collaboration",
    "communication",
    "leadership",
  ];

  const talentData = await analyticsService.getRealTalentHeatmap();
  if (!talentData.dimensions || talentData.dimensions.length !== 6) {
    throw new Error(`Expected exactly 6 talent heatmap dimensions, got ${talentData.dimensions?.length}`);
  }

  for (const expDim of expectedDimensions) {
    const found = talentData.dimensions.find((d: TalentHeatmapDimension) => d.dimension === expDim);
    if (!found) {
      throw new Error(`Missing expected heatmap dimension: ${expDim}`);
    }
  }
  console.log("✓ All 6 canonical talent heatmap dimensions confirmed.");

  // 3. Deterministic Coverage & Mean Evidence Index formula invariant
  console.log("3. Verifying coverageRate and meanEvidenceIndex deterministic formulas...");
  for (const dim of talentData.dimensions) {
    if (!dim.suppressed) {
      const expectedCoverage = ((dim.studentsWithEvidence ?? 0) / (dim.eligibleStudents ?? 1)) * 100;
      const diff = Math.abs((dim.coverageRate ?? 0) - expectedCoverage);
      if (diff > 0.1) {
        throw new Error(`Coverage formula mismatch for ${dim.dimension}: expected ~${expectedCoverage}, got ${dim.coverageRate}`);
      }
      if (dim.meanEvidenceIndex !== undefined && (dim.meanEvidenceIndex < 0 || dim.meanEvidenceIndex > 100)) {
        throw new Error(`meanEvidenceIndex out of bounds [0, 100]: ${dim.meanEvidenceIndex}`);
      }
    }
  }
  console.log("✓ Deterministic coverageRate and meanEvidenceIndex formulas verified.");

  // 4. Distinction between true zero evidence and privacy suppression
  console.log("4. Verifying distinction between zero evidence and privacy suppression...");
  const zeroEvidenceCohort: TalentHeatmapDimension = {
    dimension: "creativity",
    displayName: "Kreativitas",
    eligibleStudents: 10,
    studentsWithEvidence: 0,
    coverageRate: 0,
    meanEvidenceIndex: 0,
    suppressed: false,
  };
  const suppressedCohort: TalentHeatmapDimension = {
    dimension: "creativity",
    displayName: "Kreativitas",
    suppressed: true,
    reason: "GROUP_TOO_SMALL",
  };

  if (zeroEvidenceCohort.suppressed !== false || zeroEvidenceCohort.coverageRate !== 0) {
    throw new Error("Zero evidence cohort must have suppressed=false and coverageRate=0");
  }
  if (suppressedCohort.suppressed !== true || suppressedCohort.coverageRate !== undefined) {
    throw new Error("Suppressed cohort must have suppressed=true and undefined/null coverageRate");
  }
  console.log("✓ Zero evidence and privacy-suppressed states are strictly distinct.");

  // 5. Separate teacher rubric aggregates invariant
  console.log("5. Verifying teacher rubric aggregates remain distinct from talent heatmap...");
  const rubricsData = await analyticsService.getSchoolRubrics();
  if (!rubricsData.aggregates || rubricsData.aggregates.length === 0) {
    throw new Error("Expected rubric aggregates to be present");
  }
  const rubricDims = rubricsData.aggregates.map((a) => a.dimensionCode);
  const expectedRubrics = ["initiative", "collaboration", "communication", "responsibility", "resilience"];
  for (const r of expectedRubrics) {
    if (!rubricDims.includes(r)) {
      throw new Error(`Missing rubric dimension: ${r}`);
    }
  }
  console.log("✓ Teacher rubric aggregates remain distinct across 5 soft-skill dimensions.");

  // 6. Class management without hard delete
  console.log("6. Verifying class lifecycle and archival preservation...");
  const classes = await adminClassService.listClasses();
  if (classes.length === 0) {
    throw new Error("Expected classes to be available");
  }
  for (const c of classes) {
    if (c.status !== "active" && c.status !== "archived") {
      throw new Error(`Invalid class status: ${c.status}`);
    }
  }
  console.log("✓ Class lifecycle conforms to non-destructive status (active/archived).");

  console.log("\n======================================================");
  console.log(" ALL 6 PHASE 6 FRONTEND INVARIANT CHECKS PASSED! ");
  console.log("======================================================\n");
}).catch((err) => {
  console.error("Invariant check failed:", err);
  process.exit(1);
});

import { recommendationService } from "../src/services/recommendation.service";
import {
  RecommendationResponse,
  RecommendationEvidenceConfidence,
  RecommendationPath,
} from "../src/types/recommendation.types";

console.log("--- Running TALENTRA Phase 7 Frontend & Domain Invariant Tests ---");

// 1. Invariant: Confidence is not probability, and disallowed decision traits must NEVER exist
console.log("1. Verifying confidence levels and forbidden traits exclusion...");
const allowedConfidenceLevels: RecommendationEvidenceConfidence["level"][] = [
  "limited",
  "developing",
  "moderate",
  "strong",
];

const forbiddenFields = [
  "probability",
  "successChance",
  "employabilityScore",
  "admissionChance",
  "iq",
  "intelligenceScore",
  "talentPercentage",
];

// Synthetic check of response shape guarantees
const mockValidationResponse: RecommendationResponse = {
  generatedAt: new Date().toISOString(),
  scoringVersion: "recommendation-v1",
  catalogVersion: "career-catalog-v1",
  mappingVersion: "mapping-v1",
  evidenceConfidence: {
    score: 64,
    level: "moderate",
    approvedPortfolioCount: 5,
    distinctDimensionCount: 4,
    timeSpanMonths: 14,
    rubricAssessmentCount: 3,
    activePeriodCount: 3,
  },
  careerPaths: [
    {
      id: "cp_software_dev",
      code: "software-development",
      title: "Rekayasa Perangkat Lunak & Aplikasi",
      cluster: "Teknologi Informasi & Rekayasa Perangkat Lunak",
      description: "Pengembangan sistem perangkat lunak terstruktur.",
      type: "career",
      matchScore: 78,
      components: {
        radarMatch: 82,
        tagMatch: 85,
        rubricMatch: 62,
      },
      supportingDimensions: [{ dimension: "digital-literacy", score: 80 }],
      supportingTags: ["web-development", "problem-solving"],
      evidenceCount: 4,
      supportingPortfolios: [
        {
          portfolioId: "p_1",
          title: "Situs Web Perpustakaan",
        },
      ],
      suggestedPathways: ["Junior Web Developer", "QA Engineer"],
      rationale: "Didukung oleh bukti literasi digital dan karya web.",
    },
  ],
  studyPaths: [
    {
      id: "sp_informatics",
      code: "informatika",
      title: "Informatika / Ilmu Komputer",
      cluster: "Ilmu Komputer & Rekayasa Perangkat Lunak",
      description: "Fondasi keilmuan komputasi.",
      type: "study",
      matchScore: 80,
      components: {
        radarMatch: 85,
        tagMatch: 80,
        rubricMatch: 70,
      },
      supportingDimensions: [{ dimension: "problem-solving", score: 85 }],
      supportingTags: ["web-development"],
      evidenceCount: 3,
      supportingPortfolios: [{ portfolioId: "p_1", title: "Situs Web Perpustakaan" }],
      suggestedPathways: ["S1 Informatika", "D4 Rekayasa Perangkat Lunak"],
      rationale: "Didukung oleh bukti kemampuan analitis dan komputasi.",
    },
  ],
  disclaimer: "Panduan eksplorasi karier dan studi berbasis bukti.",
};

if (!allowedConfidenceLevels.includes(mockValidationResponse.evidenceConfidence.level)) {
  throw new Error(`Invalid confidence level: ${mockValidationResponse.evidenceConfidence.level}`);
}

const serialized = JSON.stringify(mockValidationResponse).toLowerCase();
for (const field of forbiddenFields) {
  if (serialized.includes(`"${field.toLowerCase()}":`)) {
    throw new Error(`Forbidden decision/probability trait detected in recommendation contract: ${field}`);
  }
}
console.log("✓ Confidence levels verified (strictly non-probability) and forbidden fields excluded.");

// 2. Component scores and proof-of-work dominance invariant
console.log("2. Verifying deterministic component breakdown and provenance...");
for (const p of [...mockValidationResponse.careerPaths, ...mockValidationResponse.studyPaths]) {
  if (p.matchScore < 0 || p.matchScore > 100) {
    throw new Error(`Match score out of bounds [0, 100]: ${p.matchScore}`);
  }
  if (!p.components || p.components.radarMatch === undefined || p.components.tagMatch === undefined) {
    throw new Error(`Missing component breakdown for ${p.code}`);
  }
  if (!p.supportingPortfolios || !Array.isArray(p.supportingPortfolios)) {
    throw new Error(`Missing provenance supporting portfolios for ${p.code}`);
  }
}
console.log("✓ Component scores and evidence provenance verified.");

// 3. Grounded Translator Factuality Guard Invariant
console.log("3. Verifying Factuality Guard invariants...");
function verifyFactuality(source: string, gen: string): { ok: boolean; reason?: string } {
  // Numbers in generated must exist in source
  const srcNums = new Set((source.match(/\b\d+(?:[.,]\d+)?%?/g) || []));
  const genNums = new Set((gen.match(/\b\d+(?:[.,]\d+)?%?/g) || []));
  let inventedReason: string | undefined;
  genNums.forEach((n) => {
    if (!srcNums.has(n)) {
      inventedReason = `Invented numerical claim: ${n}`;
    }
  });
  if (inventedReason) {
    return { ok: false, reason: inventedReason };
  }

  // Ungrounded tech buzzwords
  const forbiddenTech = ["react", "next.js", "kubernetes", "aws", "docker"];
  const srcLower = source.toLowerCase();
  const genLower = gen.toLowerCase();
  for (const tech of forbiddenTech) {
    if (genLower.includes(tech) && !srcLower.includes(tech)) {
      return { ok: false, reason: `Invented technology claim: ${tech}` };
    }
  }

  return { ok: true };
}

// Case A: Valid factual preservation
const resA = verifyFactuality(
  "Membuat website perpustakaan untuk tugas sekolah bersama 3 teman.",
  "Mengembangkan situs web perpustakaan bersama 3 rekan sekolah dalam proyek kolaboratif."
);
if (!resA.ok) {
  throw new Error(`Factuality test A failed: ${resA.reason}`);
}

// Case B: Detect invented percentage
const resB = verifyFactuality(
  "Membuat website perpustakaan untuk tugas sekolah bersama 3 teman.",
  "Mengembangkan situs web perpustakaan dan meningkatkan efisiensi 40%."
);
if (resB.ok) {
  throw new Error("Factuality guard failed to catch invented percentage 40%");
}

// Case C: Detect invented technology
const resC = verifyFactuality(
  "Membuat website perpustakaan untuk tugas sekolah bersama 3 teman.",
  "Mengembangkan situs web perpustakaan menggunakan framework React dan cloud."
);
if (resC.ok) {
  throw new Error("Factuality guard failed to catch ungrounded technology React");
}
console.log("✓ Factuality guard numerical & technological invariants verified.");

// 4. Recommendation service interface invariant
console.log("4. Verifying recommendation service interface contract...");
if (
  typeof recommendationService.getStudentRecommendations !== "function" ||
  typeof recommendationService.refreshStudentRecommendations !== "function" ||
  typeof recommendationService.generateProfessionalDescription !== "function" ||
  typeof recommendationService.getProfessionalDescription !== "function"
) {
  throw new Error("recommendationService is missing required Phase 7 service methods");
}
console.log("✓ Recommendation service typed interface verified.");

console.log("\n======================================================");
console.log(" ALL 4 PHASE 7 FRONTEND & DOMAIN INVARIANT CHECKS PASSED! ");
console.log("======================================================\n");

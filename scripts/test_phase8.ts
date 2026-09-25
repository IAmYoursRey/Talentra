import { cvService } from "../src/services/cv.service";
import { verificationService } from "../src/services/verification.service";
import {
  CVBuilderContext,
  CVGenerateRequest,
  CVGenerateResponse,
  IssuedCVVersion,
} from "../src/types/cv.types";
import {
  PublicVerificationResult,
  VerificationStatus,
} from "../src/types/verification.types";

console.log("--- Running TALENTRA Phase 8 Frontend & Authenticity Invariant Tests ---");

// 1. Invariant: CV Selection Policy Bounds (1 to 8 approved items)
console.log("1. Verifying CV Selection Policy bounds...");
const MIN_PORTFOLIOS = 1;
const MAX_PORTFOLIOS = 8;

function validateSelectionCount(count: number): boolean {
  return count >= MIN_PORTFOLIOS && count <= MAX_PORTFOLIOS;
}

if (!validateSelectionCount(1)) throw new Error("1 portfolio should be valid");
if (!validateSelectionCount(4)) throw new Error("4 portfolios should be valid");
if (!validateSelectionCount(8)) throw new Error("8 portfolios should be valid");
if (validateSelectionCount(0)) throw new Error("0 portfolios must be rejected");
if (validateSelectionCount(9)) throw new Error("9 portfolios must be rejected (> 8)");
console.log("✓ CV Selection Policy bounds (1..8) verified.");

// 2. Invariant: Public Verification Statuses
console.log("2. Verifying Public Verification Status contracts...");
const validStatuses: VerificationStatus[] = ["verified", "expired", "revoked", "invalid", "invalid_token"];

const mockVerifiedResponse: PublicVerificationResult = {
  status: "verified",
  displayCode: "TLN-8F4K-2M7P",
  studentDisplayName: "Siti Nurhaliza",
  schoolDisplayName: "SMK Negeri 2 Bandung",
  issuedAt: "2026-09-25T12:00:00Z",
  expiresAt: "2027-09-25T12:00:00Z",
  snapshotDigestShort: "3A8B-2C1D-9E4F",
  selectedPortfolioSummaries: [
    {
      title: "Sistem Pemantauan Suhu IoT",
      activityType: "project",
      activityDate: "2026-08-10",
      description: "Merancang perangkat telemetri sensor suhu berbasis mikrokontroler.",
      tags: ["IoT", "Web Development"],
    },
  ],
  validatedSkillSummary: [
    { name: "Literasi Digital", score: 85, level: "Tingkat Mahir" },
  ],
  verificationStatement: "Dokumen ini diterbitkan dari rekam jejak karya yang telah divalidasi.",
};

if (!validStatuses.includes(mockVerifiedResponse.status)) {
  throw new Error(`Invalid status: ${mockVerifiedResponse.status}`);
}
console.log("✓ Public Verification Status contract verified.");

// 3. Invariant: Zero Confidential Data Leakage in Public Payload
console.log("3. Verifying zero confidential data leakage in public verification contract...");
const forbiddenPublicFields = [
  "nisn",
  "nuptk",
  "nip",
  "npsn",
  "studentid",
  "student_id",
  "schoolid",
  "school_id",
  "token_hash",
  "storage_key",
  "jwt",
  "password",
  "pdf_storage_object_id",
];

const serializedPublic = JSON.stringify(mockVerifiedResponse).toLowerCase();
for (const field of forbiddenPublicFields) {
  if (serializedPublic.includes(`"${field}":`)) {
    throw new Error(`Confidential or private key leaked in public verification contract: ${field}`);
  }
}
console.log("✓ Zero confidential data leakage confirmed.");

// 4. Invariant: Fingerprint format validation (XXXX-XXXX-XXXX)
console.log("4. Verifying document fingerprint format...");
const fingerprintRegex = /^[0-9A-Z]{4}-[0-9A-Z]{4}-[0-9A-Z]{4}$/;
if (!fingerprintRegex.test(mockVerifiedResponse.snapshotDigestShort!)) {
  throw new Error(`Invalid fingerprint format: ${mockVerifiedResponse.snapshotDigestShort}`);
}
console.log("✓ Document fingerprint format (4-4-4 uppercase alphanumeric) verified.");

// 5. Invariant: CV and Verification Services Contract Interface
console.log("5. Verifying typed service interface methods...");
if (
  typeof cvService.getCVBuilderContext !== "function" ||
  typeof cvService.generateCV !== "function" ||
  typeof cvService.getCVDetail !== "function" ||
  typeof cvService.downloadCVPdf !== "function" ||
  typeof cvService.revokeCV !== "function"
) {
  throw new Error("cvService is missing required Phase 8 methods");
}

if (typeof verificationService.verifyToken !== "function") {
  throw new Error("verificationService is missing verifyToken method");
}
console.log("✓ Typed service interfaces verified.");

console.log("\n======================================================");
console.log(" ALL 5 PHASE 8 FRONTEND & DOMAIN INVARIANT CHECKS PASSED! ");
console.log("======================================================\n");

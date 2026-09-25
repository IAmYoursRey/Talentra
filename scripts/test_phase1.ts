import assert from 'assert';
import { MOCK_CANONICAL_TAGS } from '../src/mocks/canonical-tags.mock';
import { MOCK_RUBRIC_DIMENSIONS, RUBRIC_LEVEL_LABELS } from '../src/mocks/soft-skills-rubric.mock';
import { MOCK_ALL_USERS } from '../src/mocks/users.mock';
import { INITIAL_MOCK_PORTFOLIO_ITEMS } from '../src/mocks/portfolio.mock';
import { MOCK_SCHOOL_METRICS, MOCK_TALENT_HEATMAP } from '../src/mocks/analytics.mock';
import { MOCK_RECOMMENDATIONS } from '../src/mocks/recommendation.mock';
import { portfolioService } from '../src/services/portfolio.service';
import { skillService } from '../src/services/skill.service';
import { reviewService } from '../src/services/review.service';
import { verificationService } from '../src/services/verification.service';

async function runTests() {
  console.log('--- Running TALENTRA Phase 1 Acceptance & Invariant Tests ---');

  // Test 1: Canonical tags count and validity
  assert(MOCK_CANONICAL_TAGS.length >= 10, 'Must have at least 10 canonical tags');
  console.log('✓ Canonical tags catalog verified:', MOCK_CANONICAL_TAGS.length, 'tags');

  // Test 2: Rubric Dimensions and 1-5 textual meanings
  assert.strictEqual(MOCK_RUBRIC_DIMENSIONS.length, 5, 'Must have 5 soft-skill dimensions');
  ([1, 2, 3, 4, 5] as const).forEach((level) => {
    assert(RUBRIC_LEVEL_LABELS[level], `Level ${level} must have textual label`);
    MOCK_RUBRIC_DIMENSIONS.forEach((dim) => {
      assert(dim.levels[level], `Dimension ${dim.id} must define textual meaning for level ${level}`);
    });
  });
  console.log('✓ Soft skill rubric 1-5 textual definitions verified for all 5 dimensions');

  // Test 3: Privacy & Masked Identifiers
  MOCK_ALL_USERS.forEach((u) => {
    assert(u.maskedIdentifier.includes('*******'), `User ${u.name} identifier must be masked: ${u.maskedIdentifier}`);
    assert(!u.maskedIdentifier.match(/^[0-9]{10}$/), `Full 10-digit NISN must never be stored as visible identifier`);
  });
  console.log('✓ Synthetic privacy-preserving masked identifiers verified');

  // Test 4: Core Invariant 1: Unapproved evidence never affects skill radar
  const studentApproved = INITIAL_MOCK_PORTFOLIO_ITEMS.filter(
    (p) => p.studentId === 'usr_std_001' && p.status === 'approved'
  );
  const studentUnapproved = INITIAL_MOCK_PORTFOLIO_ITEMS.filter(
    (p) => p.studentId === 'usr_std_001' && p.status !== 'approved'
  );
  assert(studentApproved.length > 0, 'Must have approved items');
  assert(studentUnapproved.length > 0, 'Must have unapproved items for testing');

  const snapshot = await skillService.getStudentSkillSnapshot('usr_std_001');
  assert.strictEqual(snapshot.totalApprovedEvidence, studentApproved.length, 'Radar evidence count must match ONLY approved items');
  console.log('✓ Invariant 1 verified: Only teacher-approved evidence affects published skill scores');

  // Test 5: Tagging requirement: 3-5 tags enforcement
  INITIAL_MOCK_PORTFOLIO_ITEMS.forEach((item) => {
    assert(
      item.tags.length >= 3 && item.tags.length <= 5,
      `Item ${item.title} must have between 3 and 5 tags, found ${item.tags.length}`
    );
  });

  // Test service rejecting invalid tag count
  let errorCaught = false;
  try {
    await portfolioService.createPortfolioItem({
      title: 'Invalid Tag Test',
      activityType: 'project',
      date: '2026-09-25',
      description: 'Test item with only 1 tag',
      tags: ['web-development'], // < 3 tags!
      evidence: { type: 'link', url: 'https://github.com/test' },
      status: 'draft',
      studentId: 'usr_std_001',
      studentName: 'Alya Rahma',
      studentClass: 'XII RPL 1',
    });
  } catch (err: any) {
    errorCaught = true;
    assert(err.message.includes('3 hingga 5'), 'Should reject < 3 tags with descriptive message');
  }
  assert(errorCaught, 'Service must reject submission with fewer than 3 tags');
  console.log('✓ Strict 3-5 capability tag validation verified in service layer');

  // Test 6: Teacher Decision State Machine
  const queue = await reviewService.getReviewQueue({ status: 'submitted' });
  assert(queue.length > 0, 'Queue must contain submitted items');
  const targetItem = queue[0];
  const endorsed = await reviewService.submitReviewDecision({
    portfolioId: targetItem.id,
    action: 'endorse',
    feedback: 'Luar biasa, portofolio disetujui.',
  });
  assert.strictEqual(endorsed.status, 'approved', 'Status must transition to approved');
  console.log('✓ Teacher review decision state machine verified (submitted -> approved)');

  // Test 7: Public Verification Privacy
  const verifyValid = await verificationService.verifyToken('tlnt_token_v94b8e21');
  assert.strictEqual(verifyValid.status, 'verified', 'Token must be verified');
  assert(verifyValid.studentDisplayName, 'Must have display name');
  assert(!(verifyValid as any).nisn, 'Public verification MUST NOT expose NISN');
  assert(!(verifyValid as any).nip, 'Public verification MUST NOT expose NIP');
  assert(!(verifyValid as any).npsn, 'Public verification MUST NOT expose NPSN');

  const verifyExpired = await verificationService.verifyToken('demo-expired');
  assert.strictEqual(verifyExpired.status, 'expired', 'Expired token state verified');

  const verifyRevoked = await verificationService.verifyToken('demo-revoked');
  assert.strictEqual(verifyRevoked.status, 'revoked', 'Revoked token state verified');
  console.log('✓ Public verification privacy preservation & token states verified');

  // Test 8: Recommendations grounded in evidence
  MOCK_RECOMMENDATIONS.forEach((rec) => {
    assert(rec.evidenceCount > 0, `Recommendation ${rec.title} must have evidence count > 0`);
    assert(rec.evidenceTitles.length > 0, `Recommendation ${rec.title} must list evidence titles`);
    assert(rec.supportingSkills.length > 0, `Recommendation ${rec.title} must have supporting skills`);
  });
  console.log('✓ Recommendation engine explainability & evidence linkage verified');

  // Test 9: School Heatmap aggregates (zero individual student exposure)
  MOCK_TALENT_HEATMAP.forEach((item) => {
    assert(typeof item.studentCount === 'number', 'Heatmap item must have aggregate studentCount');
    assert(typeof item.percentage === 'number', 'Heatmap item must have aggregate percentage');
    assert(!(item as any).students, 'Heatmap must NOT contain individual student records');
  });
  console.log('✓ School talent heatmap aggregated data integrity verified');

  console.log('\n======================================================');
  console.log(' ALL 9 PHASE 1 ACCEPTANCE & INVARIANT CHECKS PASSED! ');
  console.log('======================================================\n');
}

runTests().catch((err) => {
  console.error('Test failed:', err);
  process.exit(1);
});

---
name: talentra-cv-verify
description: Generate TALENTRA digital CVs from approved evidence and implement privacy-preserving QR authenticity verification with opaque revocable tokens.
---

# CV + verification procedure

1. Build CV content from approved evidence projection only.
2. Translate activity wording only through grounded/factual transformation.
3. Snapshot the source evidence/version used to generate the CV.
4. Create an opaque high-entropy verification token; never encode NISN/NIP/NPSN.
5. Store token hash or equivalent secure verifier when appropriate to the design.
6. Generate QR URL for `/verify/<token>`.
7. Public endpoint returns only the minimal verification DTO.
8. Support revocation and clear invalid/expired states.
9. Rate-limit verification attempts.
10. Test QR on mobile-sized viewport and test token enumeration resistance assumptions.

The public page should verify authenticity, not become a public student dossier.

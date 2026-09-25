# Security & privacy reference

TALENTRA handles student records and may be used by minors. Treat identity and portfolio evidence as sensitive.

## Authentication
- Passwords: modern password hashing; never reversible encryption.
- Rate-limit login and recovery.
- Do not reveal whether a particular national identifier exists when a generic response is safer.
- JWT claims must be minimal. Role/authorization state still needs server validation.
- Avoid persistent access tokens in `localStorage`.
- Rotate/revoke refresh sessions according to chosen architecture.

## Authorization
Check:
1. authenticated user,
2. role,
3. school tenant,
4. object ownership or teacher assignment scope,
5. current workflow state,
6. action-specific policy.

## Logging
Never log:
- passwords,
- raw auth tokens,
- full NISN/NIP/NUPTK/NPSN,
- private signed object URLs,
- full CV verification secrets.

Use masked identifiers if operationally necessary.

## Upload safety
- MIME/type allowlist plus content validation where practical.
- Size limits.
- Malware scanning hook in production architecture.
- Private object storage.
- Short-lived signed access.
- Random object keys.
- Strip dangerous filename/path assumptions.

## Public verification
- QR contains an opaque high-entropy token or URL containing one.
- Verification tokens are revocable.
- Public response is minimal and versioned.
- Rate-limit enumeration.
- Do not put national identifiers in the QR.
- Do not expose private artifacts unless the student/school product policy explicitly permits them.

## Recommendation safety
- No protected traits in scoring.
- No hidden inference from unrelated personal data.
- Recommendation is guidance, not eligibility/admission determination.
- Expose evidence and scoring-rules version.
- Allow correction when source evidence is wrong.

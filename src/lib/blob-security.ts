import crypto from 'crypto';

const SECRET = process.env.JWT_SECRET_KEY || 'talentra-storage-secret';

/**
 * Validates HMAC signatures for narrow, short-lived storage operations
 * authorized by the TALENTRA platform engine (FastAPI).
 */
export function verifyBlobHmac(
  action: string,
  key: string,
  expires: number,
  signature: string
): boolean {
  const now = Math.floor(Date.now() / 1000);
  if (now > expires) {
    return false;
  }

  const expectedData = `${action}:${key}:${expires}`;
  const hmac = crypto.createHmac('sha256', SECRET);
  hmac.update(expectedData);
  const expectedSig = hmac.digest('hex');

  const expectedBuf = Buffer.from(expectedSig, 'utf-8');
  const actualBuf = Buffer.from(signature, 'utf-8');

  if (expectedBuf.length !== actualBuf.length) {
    return false;
  }

  return crypto.timingSafeEqual(expectedBuf, actualBuf);
}

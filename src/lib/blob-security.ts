import crypto from 'crypto';

/**
 * Retrieves the dedicated HMAC secret for internal FastAPI <-> Next.js Blob broker communication.
 * Strictly separate from JWT_SECRET_KEY.
 */
export function getBlobBrokerSecret(): string {
  const secret = process.env.BLOB_BROKER_HMAC_SECRET;
  if (secret && secret.length >= 32) {
    return secret;
  }
  if (process.env.APP_ENV === 'production' || process.env.NODE_ENV === 'production') {
    throw new Error('CRITICAL: BLOB_BROKER_HMAC_SECRET must be configured with >= 32 bytes in production');
  }
  return secret || 'talentra-blob-broker-dev-secret-32-bytes-min';
}

/**
 * Creates canonical signing payload for internal broker authorization.
 * Format: action|cleanPathname|expiresSeconds[|nonce]
 */
export function canonicalizeBlobPayload(
  action: string,
  pathname: string,
  expires: number,
  nonce?: string
): string {
  const cleanPath = pathname.replace(/^\/+/, '');
  return nonce ? `${action}|${cleanPath}|${expires}|${nonce}` : `${action}|${cleanPath}|${expires}`;
}

/**
 * Generates an HMAC-SHA256 signature for internal Blob broker authorization.
 */
export function createBlobHmac(
  action: string,
  pathname: string,
  expires: number,
  secretOverride?: string,
  nonce?: string
): string {
  const key = secretOverride || getBlobBrokerSecret();
  const data = canonicalizeBlobPayload(action, pathname, expires, nonce);
  return crypto.createHmac('sha256', key).update(data).digest('hex');
}

/**
 * Validates HMAC signature for internal Blob broker operations.
 * Enforces constant-time comparison and freshness bounds.
 */
export function verifyBlobHmac(
  action: string,
  pathname: string,
  expires: number,
  signature: string,
  secretOverride?: string,
  nonce?: string
): boolean {
  if (!action || !pathname || !expires || !signature) {
    return false;
  }

  const now = Math.floor(Date.now() / 1000);
  if (now > expires) {
    return false;
  }
  // Max forward TTL safety check: authorization cannot be more than 15 minutes into the future
  if (expires - now > 900) {
    return false;
  }

  try {
    const key = secretOverride || getBlobBrokerSecret();
    const expectedSig = createBlobHmac(action, pathname, expires, key, nonce);

    const expectedBuf = Buffer.from(expectedSig, 'utf-8');
    const actualBuf = Buffer.from(signature, 'utf-8');

    if (expectedBuf.length !== actualBuf.length) {
      return false;
    }

    return crypto.timingSafeEqual(expectedBuf, actualBuf);
  } catch {
    return false;
  }
}

/**
 * Validates storage object pathname to prevent path traversal or SSRF.
 */
export function validateBlobPathname(pathname: string): boolean {
  if (!pathname || typeof pathname !== 'string') {
    return false;
  }
  // Reject traversal, backslashes, absolute paths
  if (pathname.includes('..') || pathname.includes('\\') || pathname.startsWith('/')) {
    return false;
  }
  // Reject URL schemes
  if (pathname.includes('://') || /^[a-zA-Z]+:/.test(pathname)) {
    return false;
  }
  // Only allow safe alphanumeric paths with hyphen, underscore, slash, and standard extension
  const safeRegex = /^[a-zA-Z0-9_\-\/]+(\.[a-zA-Z0-9]+)?$/;
  return safeRegex.test(pathname);
}

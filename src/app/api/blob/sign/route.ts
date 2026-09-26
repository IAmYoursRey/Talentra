import { NextResponse } from 'next/server';
import { issueSignedToken, presignUrl } from '@vercel/blob';
import { verifyBlobHmac, validateBlobPathname } from '@/lib/blob-security';

interface SignRequestBody {
  action: 'get' | 'put' | 'head' | 'delete';
  pathname: string;
  expires: number;
  sig: string;
  ttl?: number;
}

const ALLOWED_ACTIONS = new Set(['get', 'put', 'head', 'delete']);

export async function POST(request: Request): Promise<NextResponse> {
  let body: SignRequestBody;
  try {
    body = (await request.json()) as SignRequestBody;
  } catch {
    return NextResponse.json({ error: 'Invalid JSON request body.' }, { status: 400 });
  }

  const { action, pathname, expires, sig, ttl } = body;

  // 1. Action allowlist validation
  if (!action || !ALLOWED_ACTIONS.has(action)) {
    return NextResponse.json(
      { error: 'Invalid or unsupported storage operation. Must be get, put, head, or delete.' },
      { status: 400 }
    );
  }

  // 2. Storage pathname validation (reject path traversal, absolute URLs, invalid chars)
  if (!pathname || !validateBlobPathname(pathname)) {
    return NextResponse.json(
      { error: 'Invalid storage pathname. Path traversal and absolute URLs are prohibited.' },
      { status: 400 }
    );
  }

  // 3. Cryptographic authorization verification (HMAC-SHA256 constant time)
  const isAuthorized = verifyBlobHmac(action, pathname, Number(expires), sig);
  if (!isAuthorized) {
    return NextResponse.json(
      { error: 'Unauthorized: invalid or expired internal storage broker signature.' },
      { status: 403 }
    );
  }

  // 4. Determine validity window (bounded between 30 and 900 seconds)
  const requestedTtl = Math.min(Math.max(Number(ttl) || 300, 30), 900);
  const validUntil = Date.now() + requestedTtl * 1000;

  // 5. Check provider authentication credentials
  const hasBlobAuth = Boolean(
    process.env.BLOB_READ_WRITE_TOKEN ||
    process.env.VERCEL_OIDC_TOKEN ||
    process.env.BLOB_STORE_ID ||
    process.env.VERCEL
  );

  if (!hasBlobAuth) {
    if (process.env.NODE_ENV === 'production' || process.env.APP_ENV === 'production') {
      return NextResponse.json(
        { error: 'Vercel Blob authentication (OIDC or BLOB_READ_WRITE_TOKEN fallback) is not configured.' },
        { status: 503 }
      );
    }
    // In local development / offline testing without cloud credentials, return synthetic URL
    const mockPresignedUrl = `https://blob.vercel-storage.com/${pathname}?operation=${action}&validUntil=${validUntil}&mock_sig=local_dev`;
    return NextResponse.json(
      { url: mockPresignedUrl, validUntil },
      { headers: { 'Cache-Control': 'private, no-store' } }
    );
  }

  // 6. Generate narrow presigned URL via official @vercel/blob boundary
  try {
    const signedToken = await issueSignedToken({
      pathname,
      operations: [action],
      validUntil,
    });

    const { presignedUrl } = await presignUrl(signedToken, {
      operation: action,
      pathname,
      access: 'private',
      validUntil,
    });

    return NextResponse.json(
      { url: presignedUrl, validUntil },
      { headers: { 'Cache-Control': 'private, no-store' } }
    );
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Unknown storage error';
    // If running in development/test mode where the store doesn't exist, provide a safe fallback URL
    if (process.env.NODE_ENV !== 'production' && process.env.APP_ENV !== 'production') {
      const mockPresignedUrl = `https://blob.vercel-storage.com/${pathname}?operation=${action}&validUntil=${validUntil}&mock_sig=local_test`;
      return NextResponse.json(
        { url: mockPresignedUrl, validUntil },
        { headers: { 'Cache-Control': 'private, no-store' } }
      );
    }

    return NextResponse.json(
      { error: `Failed to issue presigned Blob URL: ${message}` },
      { status: 500 }
    );
  }
}

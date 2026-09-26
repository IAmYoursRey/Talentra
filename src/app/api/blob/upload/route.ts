import { handleUpload, type HandleUploadBody } from '@vercel/blob/client';
import { NextResponse } from 'next/server';

const BACKEND_URL =
  process.env.API_BASE_URL ||
  (process.env.VERCEL_URL ? `https://${process.env.VERCEL_URL}` : 'http://127.0.0.1:8000');


export async function POST(request: Request): Promise<NextResponse> {
  let body: HandleUploadBody;
  try {
    body = (await request.json()) as HandleUploadBody;
  } catch {
    return NextResponse.json({ error: 'Invalid JSON request body.' }, { status: 400 });
  }

  const hasBlobAuth = Boolean(
    process.env.BLOB_READ_WRITE_TOKEN ||
    process.env.VERCEL_OIDC_TOKEN ||
    process.env.VERCEL
  );
  if (!hasBlobAuth) {
    return NextResponse.json(
      { error: 'Vercel Blob authentication (OIDC or BLOB_READ_WRITE_TOKEN fallback) is not configured.' },
      { status: 503 }
    );
  }

  try {
    const jsonResponse = await handleUpload({
      body,
      request,
      onBeforeGenerateToken: async (pathname, clientPayload) => {
        let payloadData: { intentToken?: string } = {};
        if (clientPayload) {
          try {
            payloadData = JSON.parse(clientPayload);
          } catch {
            payloadData = {};
          }
        }

        const intentToken = payloadData.intentToken;
        if (!intentToken) {
          throw new Error('Missing upload intent authorization token.');
        }

        // Verify intent with FastAPI backend which checks Neon blob_upload_intents table
        const verifyRes = await fetch(`${BACKEND_URL}/api/v1/storage/verify-intent`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token: intentToken, pathname }),
        });

        if (!verifyRes.ok) {
          const errData = await verifyRes.json().catch(() => ({}));
          throw new Error(errData?.detail?.message || 'Invalid or expired upload authorization.');
        }

        const intentInfo = await verifyRes.json();

        return {
          allowedContentTypes: ['application/pdf', 'image/jpeg', 'image/png', 'video/mp4'],
          maximumSizeInBytes: intentInfo.maxBytes || 50 * 1024 * 1024,
          tokenPayload: JSON.stringify({
            pathname,
            intentToken,
            storageObjectId: intentInfo.storageObjectId,
          }),
        };
      },
      onUploadCompleted: async () => {
        // Direct upload completed into Vercel Blob
      },
    });

    return NextResponse.json(jsonResponse);
  } catch (error) {
    return NextResponse.json(
      { error: (error as Error).message },
      { status: 400 }
    );
  }
}

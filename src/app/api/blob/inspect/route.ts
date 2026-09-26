import { head, get } from '@vercel/blob';
import { NextResponse } from 'next/server';
import { verifyBlobHmac } from '@/lib/blob-security';

export async function POST(request: Request): Promise<NextResponse> {
  try {
    const body = await request.json();
    const { key, expires, sig, maxBytes = 4096 } = body || {};

    if (!key || !expires || !sig) {
      return NextResponse.json(
        { error: 'Missing required parameters: key, expires, sig' },
        { status: 400 }
      );
    }

    if (!verifyBlobHmac('blob_inspect', key, Number(expires), String(sig))) {
      return NextResponse.json(
        { error: 'Invalid or expired storage inspection authorization.' },
        { status: 403 }
      );
    }

    const headResult = await head(key).catch(() => null);
    if (!headResult) {
      return NextResponse.json(
        { error: `Blob object '${key}' not found.` },
        { status: 404 }
      );
    }

    let magicBytesBase64 = '';
    const sliceLen = Math.min(Number(maxBytes) || 4096, 4096);

    try {
      const getResult = await get(key, { access: 'private' });
      if (getResult && getResult.stream) {
        const reader = getResult.stream.getReader();
        const chunks: Uint8Array[] = [];
        let totalRead = 0;

        while (totalRead < sliceLen) {
          const { done, value } = await reader.read();
          if (done || !value) break;
          chunks.push(value);
          totalRead += value.length;
        }

        const combined = Buffer.concat(chunks.map((c) => Buffer.from(c))).subarray(0, sliceLen);
        magicBytesBase64 = combined.toString('base64');
      }
    } catch {
      // Fallback if small read stream fails, return head metadata
    }

    return NextResponse.json({
      size: headResult.size,
      contentType: headResult.contentType,
      magicBytesBase64,
    });
  } catch (error) {
    return NextResponse.json(
      { error: (error as Error).message },
      { status: 500 }
    );
  }
}

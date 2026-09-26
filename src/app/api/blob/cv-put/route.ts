import { put } from '@vercel/blob';
import { NextRequest, NextResponse } from 'next/server';
import { verifyBlobHmac } from '@/lib/blob-security';

const CV_PDF_MAX_BYTES = Number(process.env.CV_PDF_MAX_BYTES) || 4 * 1024 * 1024; // 4 MB limit

export async function PUT(request: NextRequest): Promise<Response> {
  const searchParams = request.nextUrl.searchParams;
  const key = searchParams.get('key');
  const expires = searchParams.get('expires');
  const sig = searchParams.get('sig');

  if (!key || !expires || !sig) {
    return NextResponse.json(
      { error: 'Missing required query parameters: key, expires, sig' },
      { status: 400 }
    );
  }

  if (!verifyBlobHmac('blob_cv_put', key, Number(expires), sig)) {
    return NextResponse.json(
      { error: 'Otorisasi unggahan CV tidak valid atau telah kedaluwarsa.' },
      { status: 403 }
    );
  }

  try {
    const arrayBuffer = await request.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);

    if (buffer.length > CV_PDF_MAX_BYTES) {
      return NextResponse.json(
        { error: `Ukuran dokumen CV melebihi batas maksimum (${CV_PDF_MAX_BYTES} bytes).` },
        { status: 413 }
      );
    }

    const contentType = request.headers.get('content-type') || 'application/pdf';
    const blobResult = await put(key, buffer, {
      access: 'private',
      addRandomSuffix: false,
      contentType,
    });

    return NextResponse.json({
      status: 'success',
      url: blobResult.url,
      pathname: key,
      size: buffer.length,
    });
  } catch (error) {
    return NextResponse.json(
      { error: (error as Error).message },
      { status: 500 }
    );
  }
}

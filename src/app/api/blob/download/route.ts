import { get } from '@vercel/blob';
import { NextRequest, NextResponse } from 'next/server';
import { verifyBlobHmac } from '@/lib/blob-security';

export async function GET(request: NextRequest): Promise<Response> {
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

  if (!verifyBlobHmac('blob_download', key, Number(expires), sig)) {
    return NextResponse.json(
      { error: 'Tautan unduh tidak valid atau telah kedaluwarsa.' },
      { status: 403 }
    );
  }

  try {
    const getResult = await get(key, { access: 'private' });
    if (!getResult || !getResult.stream) {
      return NextResponse.json(
        { error: 'Berkas tidak ditemukan di penyimpanan blob.' },
        { status: 404 }
      );
    }

    const headers = new Headers();
    headers.set('Content-Type', getResult.blob.contentType || 'application/octet-stream');
    if (getResult.blob.size) {
      headers.set('Content-Length', String(getResult.blob.size));
    }
    headers.set('Cache-Control', 'no-store, no-cache, must-revalidate, private');
    headers.set('Pragma', 'no-cache');

    return new Response(getResult.stream as ReadableStream, {
      status: 200,
      headers,
    });
  } catch (error) {
    return NextResponse.json(
      { error: (error as Error).message },
      { status: 500 }
    );
  }
}

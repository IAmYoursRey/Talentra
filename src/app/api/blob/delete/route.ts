import { del } from '@vercel/blob';
import { NextResponse } from 'next/server';
import { verifyBlobHmac } from '@/lib/blob-security';

export async function POST(request: Request): Promise<NextResponse> {
  try {
    const body = await request.json();
    const { key, expires, sig } = body || {};

    if (!key || !expires || !sig) {
      return NextResponse.json(
        { error: 'Missing required parameters: key, expires, sig' },
        { status: 400 }
      );
    }

    if (!verifyBlobHmac('blob_delete', key, Number(expires), String(sig))) {
      return NextResponse.json(
        { error: 'Otorisasi penghapusan tidak valid atau telah kedaluwarsa.' },
        { status: 403 }
      );
    }

    await del(key);

    return NextResponse.json({
      deleted: true,
      key,
    });
  } catch (error) {
    return NextResponse.json(
      { error: (error as Error).message },
      { status: 500 }
    );
  }
}

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.API_BASE_URL || 'http://127.0.0.1:8000';

export async function GET(request: NextRequest) {
  try {
    const backendRes = await fetch(`${BACKEND_URL}/api/v1/auth/csrf`, {
      method: 'GET',
      headers: {
        cookie: request.headers.get('cookie') || '',
      },
    });

    if (backendRes.ok) {
      const data = await backendRes.json();
      const response = NextResponse.json(data);
      const setCookies = backendRes.headers.getSetCookie?.() || [];
      if (setCookies.length > 0) {
        setCookies.forEach((cookie) => response.headers.append('Set-Cookie', cookie));
      } else {
        const raw = backendRes.headers.get('set-cookie');
        if (raw) response.headers.set('Set-Cookie', raw);
      }
      return response;
    }
  } catch {
    // Backend offline fallback
  }

  const token = `csrf_${Math.random().toString(36).substring(2, 15)}`;
  const response = NextResponse.json({ csrfToken: token });
  response.cookies.set('talentra_csrf', token, {
    httpOnly: false,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 900,
    path: '/',
  });

  return response;
}

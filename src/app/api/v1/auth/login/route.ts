import { NextRequest, NextResponse } from 'next/server';
import { signSessionToken } from '@/lib/jwt';
import { MOCK_STUDENT, MOCK_TEACHER, MOCK_ADMIN, MOCK_ADMIN_RAIHAN } from '@/mocks/users.mock';

const BACKEND_URL = process.env.API_BASE_URL || 'http://127.0.0.1:8000';

export async function POST(request: NextRequest) {
  let body: { identifier?: string; password?: string } = {};
  try {
    body = await request.json();
  } catch {
    body = {};
  }

  const rawId = (body.identifier || '').trim();
  const trimmedLower = rawId.toLowerCase();
  const password = body.password || '';

  // 1. Try proxying to real backend if available
  try {
    const backendRes = await fetch(`${BACKEND_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ identifier: rawId, password }),
    });

    if (backendRes.status !== 500 && backendRes.status !== 502 && backendRes.status !== 503) {
      const data = await backendRes.json();
      const response = NextResponse.json(data, { status: backendRes.status });

      const setCookies = backendRes.headers.getSetCookie?.() || [];
      if (setCookies.length > 0) {
        setCookies.forEach((cookie) => {
          response.headers.append('Set-Cookie', cookie);
        });
      } else {
        const rawSetCookie = backendRes.headers.get('set-cookie');
        if (rawSetCookie) {
          response.headers.set('Set-Cookie', rawSetCookie);
        }
      }

      return response;
    }
  } catch {
    // Backend offline / connection refused -> execute robust standalone fallback
  }

  // 2. Standalone fallback credentials checking
  let matchedUser = null;
  let userRole: 'student' | 'teacher' | 'admin' = 'student';
  let redirectTo = '/student';

  if (
    trimmedLower === 'raihanansari6678@gmail.com' &&
    password === 'raihanansari6678@gmail.com'
  ) {
    userRole = 'admin';
    redirectTo = '/admin';
    matchedUser = {
      id: MOCK_ADMIN_RAIHAN.id,
      displayName: MOCK_ADMIN_RAIHAN.name,
      role: 'admin' as const,
      email: MOCK_ADMIN_RAIHAN.email,
      school: { id: 'sch_teladan_001', name: MOCK_ADMIN_RAIHAN.schoolName },
      maskedIdentifier: MOCK_ADMIN_RAIHAN.maskedIdentifier,
      className: null,
      title: MOCK_ADMIN_RAIHAN.title,
      requiresCredentialUpdate: false,
    };
  } else if (trimmedLower === '0071234321' && password === 'PasswordSiswa123!') {
    userRole = 'student';
    redirectTo = '/student';
    matchedUser = {
      id: MOCK_STUDENT.id,
      displayName: MOCK_STUDENT.name,
      role: 'student' as const,
      email: MOCK_STUDENT.email,
      school: { id: 'sch_teladan_001', name: MOCK_STUDENT.schoolName },
      maskedIdentifier: MOCK_STUDENT.maskedIdentifier,
      className: MOCK_STUDENT.className || 'XII RPL 1',
      title: null,
      requiresCredentialUpdate: false,
    };
  } else if (
    (trimmedLower === '198204152005011789' || trimmedLower === '4235760662200112') &&
    password === 'PasswordGuru123!'
  ) {
    userRole = 'teacher';
    redirectTo = '/teacher';
    matchedUser = {
      id: MOCK_TEACHER.id,
      displayName: MOCK_TEACHER.name,
      role: 'teacher' as const,
      email: MOCK_TEACHER.email,
      school: { id: 'sch_teladan_001', name: MOCK_TEACHER.schoolName },
      maskedIdentifier: MOCK_TEACHER.maskedIdentifier,
      className: null,
      title: MOCK_TEACHER.title,
      requiresCredentialUpdate: false,
    };
  } else if (trimmedLower === '20101543' && password === 'PasswordAdmin123!') {
    userRole = 'admin';
    redirectTo = '/admin';
    matchedUser = {
      id: MOCK_ADMIN.id,
      displayName: MOCK_ADMIN.name,
      role: 'admin' as const,
      email: MOCK_ADMIN.email,
      school: { id: 'sch_teladan_001', name: MOCK_ADMIN.schoolName },
      maskedIdentifier: MOCK_ADMIN.maskedIdentifier,
      className: null,
      title: MOCK_ADMIN.title,
      requiresCredentialUpdate: false,
    };
  }

  if (!matchedUser) {
    return NextResponse.json(
      {
        error: {
          code: 'AUTH_INVALID_CREDENTIALS',
          message: 'ID pengguna atau kata sandi tidak sesuai.',
        },
      },
      { status: 401 }
    );
  }

  const token = await signSessionToken({
    sub: matchedUser.id,
    role: userRole,
    school_id: 'sch_teladan_001',
  });

  const response = NextResponse.json(
    {
      user: matchedUser,
      redirectTo,
    },
    { status: 200 }
  );

  response.cookies.set('talentra_session', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 900,
    path: '/',
  });

  response.cookies.set('talentra_csrf', 'csrf_session_token', {
    httpOnly: false,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 900,
    path: '/',
  });

  return response;
}

import { NextRequest, NextResponse } from 'next/server';
import { signSessionToken } from '@/lib/jwt';
import { MOCK_STUDENT, MOCK_TEACHER, MOCK_ADMIN } from '@/mocks/users.mock';

const BACKEND_URL = process.env.API_BASE_URL || 'http://127.0.0.1:8000';

export async function POST(request: NextRequest) {
  let body: { role?: string } = {};
  try {
    body = await request.json();
  } catch {
    body = {};
  }

  // 1. Try proxying to real backend if available
  try {
    const backendRes = await fetch(`${BACKEND_URL}/api/v1/auth/demo-login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (backendRes.ok) {
      const data = await backendRes.json();
      const response = NextResponse.json(data, { status: backendRes.status });

      // Forward Set-Cookie headers
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

  // 2. Standalone fallback logic
  const role = (body.role || 'student') as 'student' | 'teacher' | 'admin';
  if (!['student', 'teacher', 'admin'].includes(role)) {
    return NextResponse.json(
      {
        error: {
          code: 'VALIDATION_ERROR',
          message: 'Format data permintaan tidak valid.',
        },
      },
      { status: 422 }
    );
  }

  const userMap = {
    student: {
      user: {
        id: MOCK_STUDENT.id,
        displayName: MOCK_STUDENT.name,
        role: 'student' as const,
        email: MOCK_STUDENT.email,
        school: { id: 'sch_teladan_001', name: MOCK_STUDENT.schoolName },
        maskedIdentifier: MOCK_STUDENT.maskedIdentifier,
        className: MOCK_STUDENT.className || 'XII RPL 1',
        title: null,
        requiresCredentialUpdate: false,
      },
      redirectTo: '/student',
    },
    teacher: {
      user: {
        id: MOCK_TEACHER.id,
        displayName: MOCK_TEACHER.name,
        role: 'teacher' as const,
        email: MOCK_TEACHER.email,
        school: { id: 'sch_teladan_001', name: MOCK_TEACHER.schoolName },
        maskedIdentifier: MOCK_TEACHER.maskedIdentifier,
        className: null,
        title: MOCK_TEACHER.title,
        requiresCredentialUpdate: false,
      },
      redirectTo: '/teacher',
    },
    admin: {
      user: {
        id: MOCK_ADMIN.id,
        displayName: MOCK_ADMIN.name,
        role: 'admin' as const,
        email: MOCK_ADMIN.email,
        school: { id: 'sch_teladan_001', name: MOCK_ADMIN.schoolName },
        maskedIdentifier: MOCK_ADMIN.maskedIdentifier,
        className: null,
        title: MOCK_ADMIN.title,
        requiresCredentialUpdate: false,
      },
      redirectTo: '/admin',
    },
  };

  const selected = userMap[role];
  const token = await signSessionToken({
    sub: selected.user.id,
    role,
    school_id: 'sch_teladan_001',
  });

  const response = NextResponse.json(selected, { status: 200 });

  // Set session cookie
  response.cookies.set('talentra_session', token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 900,
    path: '/',
  });

  // Set CSRF cookie
  response.cookies.set('talentra_csrf', 'csrf_demo_token', {
    httpOnly: false,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'lax',
    maxAge: 900,
    path: '/',
  });

  return response;
}

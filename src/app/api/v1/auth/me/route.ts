import { NextRequest, NextResponse } from 'next/server';
import { verifySessionToken } from '@/lib/jwt';
import { MOCK_STUDENT, MOCK_TEACHER, MOCK_ADMIN, MOCK_ADMIN_RAIHAN } from '@/mocks/users.mock';

const BACKEND_URL = process.env.API_BASE_URL || 'http://127.0.0.1:8000';

export async function GET(request: NextRequest) {
  // 1. Try proxying to real backend if available
  try {
    const backendRes = await fetch(`${BACKEND_URL}/api/v1/auth/me`, {
      method: 'GET',
      headers: {
        cookie: request.headers.get('cookie') || '',
      },
    });

    if (backendRes.status !== 500 && backendRes.status !== 502 && backendRes.status !== 503) {
      const data = await backendRes.json();
      return NextResponse.json(data, { status: backendRes.status });
    }
  } catch {
    // Backend offline / connection refused -> execute robust fallback
  }

  // 2. Standalone fallback based on session cookie
  const sessionCookie = request.cookies.get('talentra_session');
  if (!sessionCookie) {
    return NextResponse.json(
      { error: { code: 'AUTH_UNAUTHORIZED', message: 'Sesi tidak valid atau telah kedaluwarsa.' } },
      { status: 401 }
    );
  }

  const payload = await verifySessionToken(sessionCookie.value);
  if (!payload) {
    return NextResponse.json(
      { error: { code: 'AUTH_UNAUTHORIZED', message: 'Sesi tidak valid atau telah kedaluwarsa.' } },
      { status: 401 }
    );
  }

  if (payload.sub === MOCK_ADMIN_RAIHAN.id) {
    return NextResponse.json(
      {
        id: MOCK_ADMIN_RAIHAN.id,
        displayName: MOCK_ADMIN_RAIHAN.name,
        role: 'admin',
        email: MOCK_ADMIN_RAIHAN.email,
        school: { id: 'sch_teladan_001', name: MOCK_ADMIN_RAIHAN.schoolName },
        maskedIdentifier: MOCK_ADMIN_RAIHAN.maskedIdentifier,
        className: null,
        title: MOCK_ADMIN_RAIHAN.title,
        requiresCredentialUpdate: false,
      },
      { status: 200 }
    );
  }

  const fallbackMap = {
    student: {
      id: MOCK_STUDENT.id,
      displayName: MOCK_STUDENT.name,
      role: 'student',
      email: MOCK_STUDENT.email,
      school: { id: 'sch_teladan_001', name: MOCK_STUDENT.schoolName },
      maskedIdentifier: MOCK_STUDENT.maskedIdentifier,
      className: MOCK_STUDENT.className || 'XII RPL 1',
      title: null,
      requiresCredentialUpdate: false,
    },
    teacher: {
      id: MOCK_TEACHER.id,
      displayName: MOCK_TEACHER.name,
      role: 'teacher',
      email: MOCK_TEACHER.email,
      school: { id: 'sch_teladan_001', name: MOCK_TEACHER.schoolName },
      maskedIdentifier: MOCK_TEACHER.maskedIdentifier,
      className: null,
      title: MOCK_TEACHER.title,
      requiresCredentialUpdate: false,
    },
    admin: {
      id: MOCK_ADMIN.id,
      displayName: MOCK_ADMIN.name,
      role: 'admin',
      email: MOCK_ADMIN.email,
      school: { id: 'sch_teladan_001', name: MOCK_ADMIN.schoolName },
      maskedIdentifier: MOCK_ADMIN.maskedIdentifier,
      className: null,
      title: MOCK_ADMIN.title,
      requiresCredentialUpdate: false,
    },
  };

  return NextResponse.json(fallbackMap[payload.role] || fallbackMap.student, { status: 200 });
}

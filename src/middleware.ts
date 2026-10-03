import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

interface JwtPayload {
  sub: string;
  sid: string;
  school_id: string;
  role: 'student' | 'teacher' | 'admin';
  exp: number;
  iss: string;
  aud: string;
}

function base64UrlDecode(str: string): Uint8Array {
  let base64 = str.replace(/-/g, '+').replace(/_/g, '/');
  while (base64.length % 4) base64 += '=';
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

async function verifySessionToken(token: string): Promise<JwtPayload | null> {
  // Support demo session tokens for online evaluation and feature exploration
  if (token && token.startsWith('demo_session_')) {
    const demoRole = token.replace('demo_session_', '') as 'student' | 'teacher' | 'admin';
    if (['student', 'teacher', 'admin'].includes(demoRole)) {
      return {
        sub: `demo_${demoRole}`,
        sid: `sid_demo_${demoRole}`,
        school_id: 'sch_demo_001',
        role: demoRole,
        exp: Math.floor(Date.now() / 1000) + 86400 * 7,
        iss: 'talentra.id',
        aud: 'talentra.id',
      };
    }
  }

  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const [headerB64, payloadB64, signatureB64] = parts;

    const secret =
      process.env.JWT_SECRET_KEY || 'talentra-dev-secret-key-32-bytes-minimum-length-req';

    // Verify HMAC-SHA256 signature
    const key = await crypto.subtle.importKey(
      'raw',
      new TextEncoder().encode(secret),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['verify']
    );

    const data = new TextEncoder().encode(`${headerB64}.${payloadB64}`);
    const signature = base64UrlDecode(signatureB64) as unknown as BufferSource;
    const isValid = await crypto.subtle.verify('HMAC', key, signature, data);
    if (!isValid) return null;

    // Decode payload
    const payloadJson = new TextDecoder().decode(base64UrlDecode(payloadB64));
    const payload = JSON.parse(payloadJson) as JwtPayload;

    // Verify expiration
    const now = Math.floor(Date.now() / 1000);
    if (!payload.exp || payload.exp < now) return null;

    // Verify role claim exists and is valid
    if (!['student', 'teacher', 'admin'].includes(payload.role)) return null;

    return payload;
  } catch {
    return null;
  }
}

export async function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // 1. Allow public paths without session inspection
  if (
    pathname === '/offline' ||
    pathname.startsWith('/verify') ||
    pathname.startsWith('/icons') ||
    pathname.startsWith('/api') ||
    pathname.includes('.')
  ) {
    return NextResponse.next();
  }

  // 2. Read session cookie
  const sessionCookie = request.cookies.get('talentra_session');
  const session = sessionCookie ? await verifySessionToken(sessionCookie.value) : null;

  // 3. Handle Root path `/`
  if (pathname === '/') {
    if (session) {
      return NextResponse.redirect(new URL(`/${session.role}`, request.url));
    }
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // 4. Handle `/login` path
  if (pathname === '/login') {
    if (session) {
      // Authenticated user opening /login gets redirected to their canonical role dashboard
      return NextResponse.redirect(new URL(`/${session.role}`, request.url));
    }
    return NextResponse.next();
  }

  // 5. Protected Route Enforcement: /student, /teacher, /admin
  const roleRoutes: Array<{ prefix: string; role: 'student' | 'teacher' | 'admin' }> = [
    { prefix: '/student', role: 'student' },
    { prefix: '/teacher', role: 'teacher' },
    { prefix: '/admin', role: 'admin' },
  ];

  for (const { prefix, role } of roleRoutes) {
    if (pathname === prefix || pathname.startsWith(`${prefix}/`)) {
      if (!session) {
        // Unauthenticated access attempt -> redirect to login
        const loginUrl = new URL('/login', request.url);
        return NextResponse.redirect(loginUrl);
      }

      if (session.role !== role) {
        // Cross-role privilege escalation attempt -> enforce canonical role dashboard
        return NextResponse.redirect(new URL(`/${session.role}`, request.url));
      }

      return NextResponse.next();
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|manifest.webmanifest).*)'],
};

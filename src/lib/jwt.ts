export interface JwtPayload {
  sub: string;
  sid: string;
  school_id: string;
  role: 'student' | 'teacher' | 'admin';
  exp: number;
  iss: string;
  aud: string;
}

export function base64UrlDecode(str: string): Uint8Array {
  let base64 = str.replace(/-/g, '+').replace(/_/g, '/');
  while (base64.length % 4) base64 += '=';
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes;
}

export function base64UrlEncode(bytes: Uint8Array): string {
  let binary = '';
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

const DEFAULT_SECRET = 'talentra-dev-secret-key-32-bytes-minimum-length-req';

export async function signSessionToken(claims: {
  sub: string;
  role: 'student' | 'teacher' | 'admin';
  sid?: string;
  school_id?: string;
  expiresInSeconds?: number;
}): Promise<string> {
  const secret = process.env.JWT_SECRET_KEY || DEFAULT_SECRET;
  const now = Math.floor(Date.now() / 1000);
  const exp = now + (claims.expiresInSeconds || 15 * 60);

  const header = { alg: 'HS256', typ: 'JWT' };
  const payload: JwtPayload = {
    sub: claims.sub,
    sid: claims.sid || `sid_${Math.random().toString(36).substring(2, 10)}`,
    school_id: claims.school_id || 'sch_teladan_001',
    role: claims.role,
    iss: 'talentra.id',
    aud: 'talentra.id',
    exp,
  };

  const enc = new TextEncoder();
  const headerB64 = base64UrlEncode(enc.encode(JSON.stringify(header)));
  const payloadB64 = base64UrlEncode(enc.encode(JSON.stringify(payload)));
  const data = enc.encode(`${headerB64}.${payloadB64}`);

  const key = await crypto.subtle.importKey(
    'raw',
    enc.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signature = await crypto.subtle.sign('HMAC', key, data);
  const signatureB64 = base64UrlEncode(new Uint8Array(signature));

  return `${headerB64}.${payloadB64}.${signatureB64}`;
}

export async function verifySessionToken(token: string): Promise<JwtPayload | null> {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    const [headerB64, payloadB64, signatureB64] = parts;

    const secret = process.env.JWT_SECRET_KEY || DEFAULT_SECRET;

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

    const payloadJson = new TextDecoder().decode(base64UrlDecode(payloadB64));
    const payload = JSON.parse(payloadJson) as JwtPayload;

    const now = Math.floor(Date.now() / 1000);
    if (!payload.exp || payload.exp < now) return null;
    if (!['student', 'teacher', 'admin'].includes(payload.role)) return null;

    return payload;
  } catch {
    return null;
  }
}

export function getCsrfToken(): string {
  if (typeof document !== 'undefined') {
    const match = document.cookie.match(/(?:^|;\s*)talentra_csrf=([^;]+)/);
    if (match) return decodeURIComponent(match[1]);
  }
  return '';
}

export async function ensureCsrfToken(apiBase: string = ''): Promise<string> {
  const existing = getCsrfToken();
  if (existing) return existing;
  try {
    const res = await fetch(`${apiBase}/api/v1/auth/csrf`, {
      credentials: 'include',
    });
    if (res.ok) {
      const data = await res.json();
      return data.csrfToken || '';
    }
  } catch {
    // Graceful fallback for offline / mock testing
  }
  return '';
}

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? 'http://127.0.0.1:8000';
export class ApiError extends Error { constructor(message: string, public status = 0) { super(message); } }
export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController(); const timeout = window.setTimeout(() => controller.abort(), 30_000);
  try { const response = await fetch(`${BASE_URL}${path}`, { credentials: 'include', ...init, signal: controller.signal });
    const body: unknown = await response.json().catch(() => null);
    if (!response.ok) { const detail = body && typeof body === 'object' && 'detail' in body ? (typeof body.detail === 'string' ? body.detail : 'Please check the supplied details.') : 'The service could not complete that request.'; throw new ApiError(detail, response.status); }
    if (body && typeof body === 'object' && 'error' in body && typeof body.error === 'string') throw new ApiError(body.error, response.status);
    return body as T;
  } catch (error) { if (error instanceof ApiError) throw error; throw new ApiError(error instanceof DOMException ? 'The request timed out. Please try again.' : 'Unable to reach WeatherGPT.'); } finally { window.clearTimeout(timeout); }
}
export { BASE_URL };

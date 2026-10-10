const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export function normalizeApiError(errorData: any, fallbackMessage: string): string {
  if (typeof errorData?.detail === 'string') {
    return errorData.detail;
  }
  if (Array.isArray(errorData?.detail)) {
    // Pydantic validation error array
    return errorData.detail
      .map((err: any) => `${err.loc?.join('.') || 'field'}: ${err.msg}`)
      .join(', ');
  }
  if (typeof errorData === 'string' && errorData.trim()) {
    return errorData;
  }
  return fallbackMessage;
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const config: RequestInit = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      let errorDetail = `Request failed with status ${response.status}`;
      let errorData: any = null;

      try {
        errorData = await response.json();
        errorDetail = normalizeApiError(errorData, errorDetail);
      } catch {
        // Response was not JSON
        try {
          const text = await response.text();
          if (text) errorDetail = text;
        } catch {
          // ignore
        }
      }

      throw new ApiError(errorDetail, response.status, errorData);
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return await response.json();
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(err?.message || 'Network error occurred', 0, null);
  }
}

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
        if (typeof errorData?.detail === 'string') {
          errorDetail = errorData.detail;
        } else if (Array.isArray(errorData?.detail)) {
          // Pydantic validation error array
          errorDetail = errorData.detail
            .map((err: any) => `${err.loc?.join('.') || 'field'}: ${err.msg}`)
            .join(', ');
        }
      } catch {
        // Response was not JSON
        errorDetail = await response.text();
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

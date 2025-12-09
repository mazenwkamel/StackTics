/**
 * HTTP client for StackTics backend API.
 */

import type { OptimizeRequest, OptimizeResponse, HealthResponse } from './types';

const API_BASE_URL = 'http://localhost:8000';

/**
 * Fetch wrapper with error handling.
 */
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`API error ${response.status}: ${errorText}`);
  }

  return response.json();
}

/**
 * Check the health status of the backend.
 */
export async function checkHealth(): Promise<HealthResponse> {
  return apiFetch<HealthResponse>('/health');
}

/**
 * Run the packing optimization algorithm.
 */
export async function optimize(request: OptimizeRequest): Promise<OptimizeResponse> {
  return apiFetch<OptimizeResponse>('/optimize', {
    method: 'POST',
    body: JSON.stringify(request),
  });
}

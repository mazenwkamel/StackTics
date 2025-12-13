/**
 * HTTP client for StackTics backend API.
 */

import type { OptimizeRequest, OptimizeResponse, HealthResponse } from './types';

const API_BASE_URL = 'http://localhost:8000';

// ============================================================================
// Error Types
// ============================================================================

export interface ApiValidationErrorDetail {
  field: string;
  message: string;
  type: string;
}

export interface ApiErrorResponse {
  error: string;
  message: string;
  details: ApiValidationErrorDetail[];
}

export class ApiError extends Error {
  status: number;
  errorType: string;
  details: ApiValidationErrorDetail[];

  constructor(status: number, response: ApiErrorResponse) {
    super(response.message);
    this.name = 'ApiError';
    this.status = status;
    this.errorType = response.error;
    this.details = response.details || [];
  }

  /** Get a user-friendly error message */
  getUserMessage(): string {
    if (this.details.length > 0) {
      // Return the first few specific error messages
      const messages = this.details
        .slice(0, 3)
        .map((d) => d.message);
      if (this.details.length > 3) {
        messages.push(`...and ${this.details.length - 3} more errors`);
      }
      return messages.join('\n');
    }
    return this.message;
  }
}

// ============================================================================
// API Client
// ============================================================================

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
    // Try to parse as structured error response
    try {
      const errorData = await response.json();
      if (errorData.error && errorData.message) {
        throw new ApiError(response.status, errorData as ApiErrorResponse);
      }
    } catch (e) {
      if (e instanceof ApiError) throw e;
    }

    // Fallback for non-JSON errors
    const errorText = await response.text();
    throw new ApiError(response.status, {
      error: 'request_error',
      message: errorText || `Request failed with status ${response.status}`,
      details: [],
    });
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

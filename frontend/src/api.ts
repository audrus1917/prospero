/**
 * Error returned by the backend or an HTTP proxy.
 *
 * Keeping the status code next to the human-readable message allows callers
 * to distinguish authentication, validation, and server failures if a view
 * needs more specific handling later.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    // Restore a meaningful class name because Error defaults it to "Error".
    this.name = "ApiError";
  }
}

/**
 * Send an HTTP request to the same-origin Prospero API and decode JSON.
 *
 * The generic type describes the expected response contract at the call site.
 * Runtime response validation remains the backend's responsibility for this
 * intentionally small frontend.
 */
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  // Headers may be passed as an object, tuple list, or Headers instance, so
  // normalize them before inspecting or extending the collection.
  const headers = new Headers(options.headers);
  // Every current request body is JSON. Do not override an explicitly supplied
  // content type, which keeps this wrapper usable for other payloads later.
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(path, { ...options, headers });
  if (!response.ok) {
    // Always provide a useful fallback, even for empty or non-JSON error pages.
    let message = `Ошибка ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      message = body.detail ?? message;
    } catch {
      // Preserve the HTTP status when an upstream proxy returns a non-JSON body.
    }
    throw new ApiError(message, response.status);
  }
  // Successful API endpoints used by the UI always return a JSON document.
  return (await response.json()) as T;
}

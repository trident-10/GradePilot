/**
 * Central API configuration.
 * Canonical local backend: http://127.0.0.1:8000
 * Set NEXT_PUBLIC_API_BASE_URL in .env.local only if you must override it.
 * Do not use port 8001 as a normal application dependency.
 */
export function getApiBaseUrl(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  if (configured) {
    return configured.replace(/\/$/, "");
  }
  return "http://127.0.0.1:8000";
}

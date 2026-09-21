import { supabase } from "@/lib/supabase";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function parseErrorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    const detail = body.detail;
    if (typeof detail === "string") {
      return detail;
    }
    // FastAPI/Pydantic validation errors (422) return `detail` as an array of
    // {msg, loc, ...} objects rather than a plain string — stringify those into
    // something readable instead of letting them coerce to "[object Object]".
    if (Array.isArray(detail)) {
      const messages = detail.map((err) => {
        const msg = typeof err?.msg === "string" ? err.msg : JSON.stringify(err);
        return msg.replace(/^Value error, /, "");
      });
      return messages.join(" ") || response.statusText;
    }
    return response.statusText;
  } catch {
    return response.statusText;
  }
}

export async function apiFetch(path: string, options: RequestInit = {}, retry = true): Promise<Response> {
  // supabase-js refreshes the access token in the background, so getSession() is current
  const { data } = await supabase.auth.getSession();
  const accessToken = data.session?.access_token;
  const headers = new Headers(options.headers);
  if (accessToken) {
    headers.set("Authorization", `Bearer ${accessToken}`);
  }
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (response.status === 401 && retry) {
    const { data: refreshed } = await supabase.auth.refreshSession();
    if (refreshed.session) {
      return apiFetch(path, options, false);
    }
  }

  return response;
}

export async function apiJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await apiFetch(path, options);
  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorMessage(response));
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

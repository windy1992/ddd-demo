import { API_BASE } from "@/lib/config"

const TOKEN_KEY = "iam_access_token"

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

async function readErrorMessage(res: Response): Promise<string> {
  try {
    const data: unknown = await res.json()
    if (
      data &&
      typeof data === "object" &&
      "message" in data &&
      typeof (data as { message: unknown }).message === "string"
    ) {
      return (data as { message: string }).message
    }
  } catch {
    /* ignore */
  }
  return res.statusText || "请求失败"
}

export type ApiFetchOptions = RequestInit & {
  /** 不附加 Authorization（如登录） */
  skipAuth?: boolean
}

export async function apiFetch<T>(
  path: string,
  init: ApiFetchOptions = {},
): Promise<T> {
  const { skipAuth, headers: initHeaders, ...rest } = init
  const url = `${API_BASE}${path.startsWith("/") ? path : `/${path}`}`
  const headers = new Headers(initHeaders)

  if (!skipAuth) {
    const t = getToken()
    if (t) headers.set("Authorization", `Bearer ${t}`)
  }

  const res = await fetch(url, { ...rest, headers, cache: "no-store" })

  if (res.status === 401) {
    clearToken()
    if (!path.includes("/auth/login")) {
      window.location.assign(`${window.location.origin}/login`)
    }
    throw new Error(await readErrorMessage(res))
  }

  if (!res.ok) {
    throw new Error(await readErrorMessage(res))
  }

  const text = await res.text()
  if (!text) return undefined as T
  return JSON.parse(text) as T
}

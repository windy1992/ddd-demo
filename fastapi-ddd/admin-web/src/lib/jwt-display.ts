/** 仅用于界面展示，不做签名校验 */
export function decodeJwtPayload(token: string): {
  user_id?: string
  user_name?: string
  role_names?: string[]
} | null {
  try {
    const part = token.split(".")[1]
    if (!part) return null
    const b64 = part.replace(/-/g, "+").replace(/_/g, "/")
    const json = decodeURIComponent(
      atob(b64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join(""),
    )
    return JSON.parse(json) as {
      user_id?: string
      user_name?: string
      role_names?: string[]
    }
  } catch {
    return null
  }
}

import { useEffect, useState } from "react"
import { NavLink, Navigate, Outlet, useNavigate } from "react-router-dom"

import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { clearToken, getToken } from "@/lib/api-client"
import { decodeJwtPayload } from "@/lib/jwt-display"
import { listUsers } from "@/lib/iam-api"

const navCls =
  "block rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
const activeCls = "bg-accent text-accent-foreground"

export function AdminLayout() {
  const navigate = useNavigate()
  const token = getToken()

  const [displayName, setDisplayName] = useState("—")

  useEffect(() => {
    if (!token) return
    const p = decodeJwtPayload(token)
    const fromJwt = p?.user_name?.trim()
    if (fromJwt) {
      setDisplayName(fromJwt)
      return
    }
    const uid = p?.user_id
    if (!uid) {
      setDisplayName("—")
      return
    }
    let cancelled = false
    void (async () => {
      try {
        const users = await listUsers()
        if (cancelled) return
        const row = users.find((u) => u.user_id === uid)
        setDisplayName(row?.user_name?.trim() || "—")
      } catch {
        if (!cancelled) setDisplayName("—")
      }
    })()
    return () => {
      cancelled = true
    }
  }, [token])

  if (!token) {
    return <Navigate to="/login" replace />
  }

  const payload = decodeJwtPayload(token)
  const roleSummary =
    payload?.role_names && payload.role_names.length > 0
      ? payload.role_names.join("、")
      : "—"

  function logout() {
    clearToken()
    navigate("/login", { replace: true })
  }

  return (
    <div className="flex min-h-svh flex-col md:flex-row">
      <aside className="border-b bg-card md:w-56 md:border-b-0 md:border-r">
        <div className="flex h-14 items-center px-4 font-semibold">IAM 管理</div>
        <Separator />
        <nav className="flex flex-row gap-1 p-2 md:flex-col">
          <NavLink
            to="/users"
            className={({ isActive }) => `${navCls} ${isActive ? activeCls : ""}`}
          >
            用户
          </NavLink>
          <NavLink
            to="/roles"
            className={({ isActive }) => `${navCls} ${isActive ? activeCls : ""}`}
          >
            角色
          </NavLink>
          <NavLink
            to="/permissions"
            className={({ isActive }) => `${navCls} ${isActive ? activeCls : ""}`}
          >
            权限
          </NavLink>
        </nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b bg-background px-4">
          <span className="text-sm text-muted-foreground">
            用户名：
            <span className="text-foreground">{displayName}</span>
            <span className="mx-2 text-border">|</span>
            角色：
            <span className="text-foreground">{roleSummary}</span>
          </span>
          <Button type="button" variant="outline" size="sm" onClick={logout}>
            退出
          </Button>
        </header>
        <main className="flex-1 overflow-auto p-4 md:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

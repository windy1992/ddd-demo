import { apiFetch } from "@/lib/api-client"
import type {
  PermissionBase,
  RoleInfo,
  TokenResponse,
  UserInfo,
} from "@/lib/iam-types"

export async function login(username: string, password: string) {
  const body = new URLSearchParams({ username, password })
  return apiFetch<TokenResponse>("/auth/login", {
    method: "POST",
    skipAuth: true,
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  })
}

/** 登录后探活：仅 admin 可访问列表 */
export function probeAdminAccess() {
  return apiFetch<UserInfo[]>("/auth/users")
}

export function registerUser(username: string, password: string) {
  return apiFetch<unknown>("/auth/user", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  })
}

export function listUsers() {
  return apiFetch<UserInfo[]>("/auth/users")
}

export function listRoles() {
  return apiFetch<RoleInfo[]>("/auth/roles")
}

export function listPermissions() {
  return apiFetch<PermissionBase[]>("/auth/permissions")
}

export function createRole(role_name: string) {
  return apiFetch<unknown>("/auth/role", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role_name }),
  })
}

export function createPermission(code: string) {
  return apiFetch<unknown>("/auth/permission", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  })
}

export function assignRolesToUser(user_name: string, role_ids: string[]) {
  return apiFetch<unknown>(`/auth/users/${encodeURIComponent(user_name)}/roles`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role_ids }),
  })
}

export function revokeRolesFromUser(user_id: string, role_ids: string[]) {
  return apiFetch<unknown>(`/auth/users/${encodeURIComponent(user_id)}/roles`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ role_ids }),
  })
}

export function assignPermissionsToRole(role_id: string, permission_ids: string[]) {
  return apiFetch<unknown>(`/auth/roles/${encodeURIComponent(role_id)}/permissions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ permission_ids }),
  })
}

export function revokePermissionsFromRole(role_id: string, permission_ids: string[]) {
  return apiFetch<unknown>(`/auth/roles/${encodeURIComponent(role_id)}/permissions`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ permission_ids }),
  })
}

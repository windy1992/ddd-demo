export interface PaginatedResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export interface RoleBase {
  role_id: string
  role_name: string
}

export interface PermissionBase {
  permission_id: string
  code: string
}

export interface UserInfo {
  user_id: string
  user_name: string
  roles: RoleBase[]
}

export interface RoleInfo extends RoleBase {
  permissions: PermissionBase[]
}

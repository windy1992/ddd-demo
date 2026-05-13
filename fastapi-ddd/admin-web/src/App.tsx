import { Navigate, Route, Routes } from "react-router-dom"

import { AdminLayout } from "@/pages/AdminLayout"
import { LoginPage } from "@/pages/LoginPage"
import { PermissionsPage } from "@/pages/PermissionsPage"
import { RolesPage } from "@/pages/RolesPage"
import { UsersPage } from "@/pages/UsersPage"

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<AdminLayout />}>
        <Route index element={<Navigate to="users" replace />} />
        <Route path="users" element={<UsersPage />} />
        <Route path="roles" element={<RolesPage />} />
        <Route path="permissions" element={<PermissionsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

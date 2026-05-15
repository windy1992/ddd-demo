import { useCallback, useEffect, useState } from "react"
import { toast } from "sonner"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { PaginationBar } from "@/components/ui/pagination-bar"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { PermissionBase, RoleInfo } from "@/lib/iam-types"
import {
  assignPermissionsToRole,
  createRole,
  deleteRole,
  listPermissions,
  listRolesPaged,
  revokePermissionsFromRole,
} from "@/lib/iam-api"

const DEFAULT_PAGE_SIZE = 10

export function RolesPage() {
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [perms, setPerms] = useState<PermissionBase[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [total, setTotal] = useState(0)

  const [createOpen, setCreateOpen] = useState(false)
  const [newName, setNewName] = useState("")

  const [assignOpen, setAssignOpen] = useState(false)
  const [revokeOpen, setRevokeOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [activeRole, setActiveRole] = useState<RoleInfo | null>(null)
  const [picked, setPicked] = useState<Set<string>>(new Set())
  const [assignPermBaseline, setAssignPermBaseline] = useState<Set<string>>(new Set())

  const load = useCallback(async (p = page, ps = pageSize) => {
    setLoading(true)
    try {
      const [paged, permsData] = await Promise.all([listRolesPaged(p, ps), listPermissions()])
      setRoles(paged.items)
      setTotal(paged.total)
      setPerms(permsData)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "加载失败")
    } finally {
      setLoading(false)
    }
  }, [page, pageSize])

  useEffect(() => {
    void load()
  }, [load])

  function handlePageChange(p: number) {
    setPage(p)
  }

  function handlePageSizeChange(ps: number) {
    setPageSize(ps)
    setPage(1)
  }

  function openAssign(role: RoleInfo) {
    setActiveRole(role)
    const already = new Set(role.permissions.map((p) => p.permission_id))
    setAssignPermBaseline(already)
    setPicked(new Set(already))
    setAssignOpen(true)
  }

  function openRevoke(role: RoleInfo) {
    setActiveRole(role)
    setPicked(new Set())
    setRevokeOpen(true)
  }

  function openDelete(role: RoleInfo) {
    setActiveRole(role)
    setDeleteOpen(true)
  }

  async function submitDelete() {
    if (!activeRole) return
    try {
      await deleteRole(activeRole.role_id)
      toast.success("角色已删除")
      setDeleteOpen(false)
      const newTotal = total - 1
      const maxPage = Math.max(1, Math.ceil(newTotal / pageSize))
      const targetPage = page > maxPage ? maxPage : page
      setPage(targetPage)
      await load(targetPage, pageSize)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "删除失败")
    }
  }

  function toggle(id: string, checked: boolean) {
    setPicked((prev) => {
      const next = new Set(prev)
      if (checked) next.add(id)
      else next.delete(id)
      return next
    })
  }

  async function submitCreate() {
    if (!newName.trim()) {
      toast.warning("请输入角色名")
      return
    }
    try {
      await createRole(newName.trim())
      toast.success("角色已创建")
      setNewName("")
      setCreateOpen(false)
      await load(page, pageSize)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "创建失败")
    }
  }

  async function submitAssign() {
    if (!activeRole) return
    const toAdd = [...picked].filter((id) => !assignPermBaseline.has(id))
    if (toAdd.length === 0) {
      toast.info("未勾选新的权限（已分配的权限保持勾选即可）")
      return
    }
    try {
      await assignPermissionsToRole(activeRole.role_id, toAdd)
      toast.success("权限已分配")
      setAssignOpen(false)
      await load(page, pageSize)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "分配失败")
    }
  }

  async function submitRevoke() {
    if (!activeRole) return
    const ids = [...picked]
    if (ids.length === 0) {
      toast.warning("请选择要移除的权限")
      return
    }
    try {
      await revokePermissionsFromRole(activeRole.role_id, ids)
      toast.success("已移除权限")
      setRevokeOpen(false)
      await load(page, pageSize)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "移除失败")
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-lg font-semibold">角色管理</h1>
        <div className="flex gap-2">
          <Button type="button" variant="outline" size="sm" onClick={() => void load(page, pageSize)}>
            刷新
          </Button>
          <Button type="button" size="sm" onClick={() => setCreateOpen(true)}>
            新建角色
          </Button>
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>角色名</TableHead>
              <TableHead>权限</TableHead>
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={3} className="text-center text-muted-foreground">
                  加载中…
                </TableCell>
              </TableRow>
            ) : roles.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-center text-muted-foreground">
                  暂无角色
                </TableCell>
              </TableRow>
            ) : (
              roles.map((r) => (
                <TableRow key={r.role_id}>
                  <TableCell>
                    <div className="font-medium">{r.role_name}</div>
                    <div className="font-mono text-xs text-muted-foreground">{r.role_id}</div>
                  </TableCell>
                  <TableCell>
                    <div className="flex max-w-xl flex-wrap gap-1">
                      {r.permissions.length === 0 ? (
                        <span className="text-muted-foreground">—</span>
                      ) : (
                        r.permissions.map((p) => (
                          <Badge key={p.permission_id} variant="outline">
                            {p.code}
                          </Badge>
                        ))
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex flex-wrap justify-end gap-2">
                      <Button type="button" variant="outline" size="sm" onClick={() => openAssign(r)}>
                        分配权限
                      </Button>
                      <Button type="button" variant="outline" size="sm" onClick={() => openRevoke(r)}>
                        移除权限
                      </Button>
                      <Button type="button" variant="destructive" size="sm" onClick={() => openDelete(r)}>
                        删除
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
        <PaginationBar
          page={page}
          pageSize={pageSize}
          total={total}
          onChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
        />
      </div>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建角色</DialogTitle>
          </DialogHeader>
          <div className="grid gap-2 py-2">
            <Label htmlFor="rn">角色名</Label>
            <Input id="rn" value={newName} onChange={(e) => setNewName(e.target.value)} />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>
              取消
            </Button>
            <Button type="button" onClick={() => void submitCreate()}>
              创建
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={assignOpen} onOpenChange={setAssignOpen}>
        <DialogContent className="max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>分配权限（{activeRole?.role_name}）</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            已勾选表示当前拥有或即将分配的权限；仅对新勾选的权限调用接口。
          </p>
          <div className="grid gap-3 py-2">
            {perms.map((p) => {
              const already = assignPermBaseline.has(p.permission_id)
              return (
                <label
                  key={p.permission_id}
                  className={`flex flex-wrap items-center gap-2 rounded-md border p-2 ${already ? "cursor-not-allowed opacity-70" : "cursor-pointer"}`}
                >
                  <Checkbox
                    checked={picked.has(p.permission_id)}
                    disabled={already}
                    onCheckedChange={(c) => toggle(p.permission_id, c === true)}
                  />
                  <span className="text-sm">{p.code}</span>
                  {already ? (
                    <Badge variant="secondary" className="text-xs">
                      已分配
                    </Badge>
                  ) : null}
                </label>
              )
            })}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setAssignOpen(false)}>
              取消
            </Button>
            <Button type="button" onClick={() => void submitAssign()}>
              确认分配
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>删除角色</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            确定要删除角色 <span className="font-medium text-foreground">{activeRole?.role_name}</span> 吗？此操作不可撤销。
          </p>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setDeleteOpen(false)}>
              取消
            </Button>
            <Button type="button" variant="destructive" onClick={() => void submitDelete()}>
              确认删除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={revokeOpen} onOpenChange={setRevokeOpen}>
        <DialogContent className="max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>移除权限（{activeRole?.role_name}）</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            下列均为当前已拥有的权限，请勾选要移除的项。
          </p>
          <div className="grid gap-3 py-2">
            {(activeRole?.permissions ?? []).map((p) => (
              <label
                key={p.permission_id}
                className="flex cursor-pointer flex-wrap items-center gap-2 rounded-md border p-2"
              >
                <Checkbox
                  checked={picked.has(p.permission_id)}
                  onCheckedChange={(c) => toggle(p.permission_id, c === true)}
                />
                <span className="text-sm">{p.code}</span>
                <Badge variant="outline" className="text-xs">
                  已分配
                </Badge>
              </label>
            ))}
            {(activeRole?.permissions?.length ?? 0) === 0 && (
              <p className="text-sm text-muted-foreground">该角色暂无权限可移除</p>
            )}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setRevokeOpen(false)}>
              取消
            </Button>
            <Button type="button" variant="destructive" onClick={() => void submitRevoke()}>
              确认移除
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

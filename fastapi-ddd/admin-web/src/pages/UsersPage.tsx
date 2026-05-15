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
import type { RoleInfo, UserInfo } from "@/lib/iam-types"
import {
  assignRolesToUser,
  deleteUser,
  listRoles,
  listUsersPaged,
  registerUser,
  revokeRolesFromUser,
} from "@/lib/iam-api"

const DEFAULT_PAGE_SIZE = 10

export function UsersPage() {
  const [users, setUsers] = useState<UserInfo[]>([])
  const [roles, setRoles] = useState<RoleInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [total, setTotal] = useState(0)

  const [registerOpen, setRegisterOpen] = useState(false)
  const [regUser, setRegUser] = useState("")
  const [regPass, setRegPass] = useState("")

  const [assignOpen, setAssignOpen] = useState(false)
  const [revokeOpen, setRevokeOpen] = useState(false)
  const [deleteOpen, setDeleteOpen] = useState(false)
  const [activeUser, setActiveUser] = useState<UserInfo | null>(null)
  const [pickedRoles, setPickedRoles] = useState<Set<string>>(new Set())
  const [assignRoleBaseline, setAssignRoleBaseline] = useState<Set<string>>(new Set())

  const load = useCallback(async (p = page, ps = pageSize) => {
    setLoading(true)
    try {
      const [paged, r] = await Promise.all([listUsersPaged(p, ps), listRoles()])
      setUsers(paged.items)
      setTotal(paged.total)
      setRoles(r)
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

  function openAssign(user: UserInfo) {
    setActiveUser(user)
    const already = new Set(user.roles.map((r) => r.role_id))
    setAssignRoleBaseline(already)
    setPickedRoles(new Set(already))
    setAssignOpen(true)
  }

  function openRevoke(user: UserInfo) {
    setActiveUser(user)
    setPickedRoles(new Set())
    setRevokeOpen(true)
  }

  function openDelete(user: UserInfo) {
    setActiveUser(user)
    setDeleteOpen(true)
  }

  async function submitDelete() {
    if (!activeUser) return
    try {
      await deleteUser(activeUser.user_id)
      toast.success("用户已删除")
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

  function toggleRole(id: string, checked: boolean) {
    setPickedRoles((prev) => {
      const next = new Set(prev)
      if (checked) next.add(id)
      else next.delete(id)
      return next
    })
  }

  async function submitRegister() {
    try {
      await registerUser(regUser, regPass)
      toast.success("用户已注册")
      setRegUser("")
      setRegPass("")
      setRegisterOpen(false)
      await load(page, pageSize)
    } catch (e) {
      setRegUser("")
      setRegPass("")
      toast.error(e instanceof Error ? e.message : "注册失败")
    }
  }

  async function submitAssign() {
    if (!activeUser) return
    const toAdd = [...pickedRoles].filter((id) => !assignRoleBaseline.has(id))
    if (toAdd.length === 0) {
      toast.info("未勾选新的角色（已分配的角色保持勾选即可）")
      return
    }
    try {
      await assignRolesToUser(activeUser.user_id, toAdd)
      toast.success("角色已分配")
      setAssignOpen(false)
      await load(page, pageSize)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "分配失败")
    }
  }

  async function submitRevoke() {
    if (!activeUser) return
    const ids = [...pickedRoles]
    if (ids.length === 0) {
      toast.warning("请选择要移除的角色")
      return
    }
    try {
      await revokeRolesFromUser(activeUser.user_id, ids)
      toast.success("已移除角色")
      setRevokeOpen(false)
      await load(page, pageSize)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "移除失败")
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-lg font-semibold">用户管理</h1>
        <div className="flex gap-2">
          <Button type="button" variant="outline" size="sm" onClick={() => void load(page, pageSize)}>
            刷新
          </Button>
          <Button type="button" size="sm" onClick={() => setRegisterOpen(true)}>
            注册用户
          </Button>
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>用户 ID</TableHead>
              <TableHead>用户名</TableHead>
              <TableHead>角色</TableHead>
              <TableHead className="text-right">操作</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  加载中…
                </TableCell>
              </TableRow>
            ) : users.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center text-muted-foreground">
                  暂无用户
                </TableCell>
              </TableRow>
            ) : (
              users.map((u) => (
                <TableRow key={u.user_id}>
                  <TableCell className="font-mono text-xs">{u.user_id}</TableCell>
                  <TableCell>{u.user_name}</TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {u.roles.length === 0 ? (
                        <span className="text-muted-foreground">—</span>
                      ) : (
                        u.roles.map((r) => (
                          <Badge key={r.role_id} variant="secondary">
                            {r.role_name}
                          </Badge>
                        ))
                      )}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex flex-wrap justify-end gap-2">
                      <Button type="button" variant="outline" size="sm" onClick={() => openAssign(u)}>
                        分配角色
                      </Button>
                      <Button type="button" variant="outline" size="sm" onClick={() => openRevoke(u)}>
                        移除角色
                      </Button>
                      <Button type="button" variant="destructive" size="sm" onClick={() => openDelete(u)}>
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

      <Dialog open={registerOpen} onOpenChange={setRegisterOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>注册用户</DialogTitle>
          </DialogHeader>
          <div className="grid gap-4 py-2">
            <div className="grid gap-2">
              <Label htmlFor="reg-u">用户名</Label>
              <Input
                id="reg-u"
                value={regUser}
                onChange={(e) => setRegUser(e.target.value)}
              />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="reg-p">密码</Label>
              <Input
                id="reg-p"
                type="password"
                value={regPass}
                onChange={(e) => setRegPass(e.target.value)}
              />
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setRegisterOpen(false)}>
              取消
            </Button>
            <Button type="button" onClick={() => void submitRegister()}>
              提交
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={assignOpen} onOpenChange={setAssignOpen}>
        <DialogContent className="max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>分配角色（{activeUser?.user_name}）</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            已勾选表示当前拥有或即将分配的角色；仅对新勾选的角色调用接口。
          </p>
          <div className="grid gap-3 py-2">
            {roles.map((r) => {
              const already = assignRoleBaseline.has(r.role_id)
              return (
                <label
                  key={r.role_id}
                  className={`flex items-center gap-2 rounded-md border p-2 ${already ? "cursor-not-allowed opacity-70" : "cursor-pointer"}`}
                >
                  <Checkbox
                    checked={pickedRoles.has(r.role_id)}
                    disabled={already}
                    onCheckedChange={(c) => toggleRole(r.role_id, c === true)}
                  />
                  <span className="font-medium">{r.role_name}</span>
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
            <DialogTitle>删除用户</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            确定要删除用户 <span className="font-medium text-foreground">{activeUser?.user_name}</span> 吗？此操作不可撤销。
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
            <DialogTitle>移除角色（{activeUser?.user_name}）</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            下列均为当前已拥有的角色，请勾选要移除的项。
          </p>
          <div className="grid gap-3 py-2">
            {(activeUser?.roles ?? []).map((r) => (
              <label
                key={r.role_id}
                className="flex cursor-pointer items-center gap-2 rounded-md border p-2"
              >
                <Checkbox
                  checked={pickedRoles.has(r.role_id)}
                  onCheckedChange={(c) => toggleRole(r.role_id, c === true)}
                />
                <span className="font-medium">{r.role_name}</span>
                <Badge variant="outline" className="text-xs">
                  已分配
                </Badge>
              </label>
            ))}
            {(activeUser?.roles?.length ?? 0) === 0 && (
              <p className="text-sm text-muted-foreground">该用户暂无角色可移除</p>
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

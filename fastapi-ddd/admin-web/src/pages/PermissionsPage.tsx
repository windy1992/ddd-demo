import { useCallback, useEffect, useState } from "react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
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
import type { PermissionBase } from "@/lib/iam-types"
import { createPermission, deletePermission, listPermissionsPaged } from "@/lib/iam-api"

const DEFAULT_PAGE_SIZE = 10

export function PermissionsPage() {
  const [rows, setRows] = useState<PermissionBase[]>([])
  const [loading, setLoading] = useState(true)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [total, setTotal] = useState(0)

  const [open, setOpen] = useState(false)
  const [code, setCode] = useState("")

  const [deleteOpen, setDeleteOpen] = useState(false)
  const [activePerm, setActivePerm] = useState<PermissionBase | null>(null)

  const load = useCallback(async (p = page, ps = pageSize) => {
    setLoading(true)
    try {
      const paged = await listPermissionsPaged(p, ps)
      setRows(paged.items)
      setTotal(paged.total)
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

  async function submit() {
    if (!code.trim()) {
      toast.warning("请输入权限 code")
      return
    }
    try {
      await createPermission(code.trim())
      toast.success("权限已创建")
      setOpen(false)
      setCode("")
      await load(page, pageSize)
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "创建失败")
    }
  }

  function openDelete(perm: PermissionBase) {
    setActivePerm(perm)
    setDeleteOpen(true)
  }

  async function submitDelete() {
    if (!activePerm) return
    try {
      await deletePermission(activePerm.permission_id)
      toast.success("权限已删除")
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

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-lg font-semibold">权限管理</h1>
        <div className="flex gap-2">
          <Button type="button" variant="outline" size="sm" onClick={() => void load(page, pageSize)}>
            刷新
          </Button>
          <Button type="button" size="sm" onClick={() => setOpen(true)}>
            新建权限
          </Button>
        </div>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>权限 ID</TableHead>
              <TableHead>Code</TableHead>
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
            ) : rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="text-center text-muted-foreground">
                  暂无权限
                </TableCell>
              </TableRow>
            ) : (
              rows.map((p) => (
                <TableRow key={p.permission_id}>
                  <TableCell className="font-mono text-xs">{p.permission_id}</TableCell>
                  <TableCell className="font-mono text-sm">{p.code}</TableCell>
                  <TableCell className="text-right">
                    <Button type="button" variant="destructive" size="sm" onClick={() => openDelete(p)}>
                      删除
                    </Button>
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

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>新建权限</DialogTitle>
          </DialogHeader>
          <div className="grid gap-2 py-2">
            <Label htmlFor="pc">权限 code</Label>
            <Input id="pc" value={code} onChange={(e) => setCode(e.target.value)} />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setOpen(false)}>
              取消
            </Button>
            <Button type="button" onClick={() => void submit()}>
              创建
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={deleteOpen} onOpenChange={setDeleteOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>删除权限</DialogTitle>
          </DialogHeader>
          <p className="text-sm text-muted-foreground">
            确定要删除权限 <span className="font-medium text-foreground">{activePerm?.code}</span> 吗？此操作不可撤销。
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
    </div>
  )
}

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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { PermissionBase } from "@/lib/iam-types"
import { createPermission, listPermissions } from "@/lib/iam-api"

export function PermissionsPage() {
  const [rows, setRows] = useState<PermissionBase[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [code, setCode] = useState("")

  const load = useCallback(async () => {
    setLoading(true)
    try {
      setRows(await listPermissions())
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "加载失败")
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

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
      await load()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "创建失败")
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-lg font-semibold">权限管理</h1>
        <div className="flex gap-2">
          <Button type="button" variant="outline" size="sm" onClick={() => void load()}>
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
            </TableRow>
          </TableHeader>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={2} className="text-center text-muted-foreground">
                  加载中…
                </TableCell>
              </TableRow>
            ) : rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={2} className="text-center text-muted-foreground">
                  暂无权限
                </TableCell>
              </TableRow>
            ) : (
              rows.map((p) => (
                <TableRow key={p.permission_id}>
                  <TableCell className="font-mono text-xs">{p.permission_id}</TableCell>
                  <TableCell className="font-mono text-sm">{p.code}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
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
    </div>
  )
}

import { Button } from "@/components/ui/button"

const PAGE_SIZE_OPTIONS = [10, 20, 50, 100]

interface PaginationBarProps {
  page: number
  pageSize: number
  total: number
  onChange: (page: number) => void
  onPageSizeChange?: (pageSize: number) => void
}

export function PaginationBar({
  page,
  pageSize,
  total,
  onChange,
  onPageSizeChange,
}: PaginationBarProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize))
  const start = total === 0 ? 0 : (page - 1) * pageSize + 1
  const end = Math.min(page * pageSize, total)

  return (
    <div className="flex flex-wrap items-center justify-between gap-2 px-2 py-2 text-sm text-muted-foreground">
      <div className="flex items-center gap-2">
        <span>共 {total} 条，第 {start}–{end} 条</span>
        {onPageSizeChange && (
          <select
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="rounded border border-input bg-background px-2 py-1 text-sm focus:outline-none"
          >
            {PAGE_SIZE_OPTIONS.map((s) => (
              <option key={s} value={s}>
                {s} 条/页
              </option>
            ))}
          </select>
        )}
      </div>
      <div className="flex items-center gap-1">
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
        >
          上一页
        </Button>
        <span className="px-2">
          {page} / {totalPages}
        </span>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={page >= totalPages}
          onClick={() => onChange(page + 1)}
        >
          下一页
        </Button>
      </div>
    </div>
  )
}

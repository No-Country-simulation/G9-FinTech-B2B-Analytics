import { ChevronLeftIcon, ChevronRightIcon } from "lucide-react"

import { Button } from "@/components/ui/button"

export function TablePagination({
  page,
  size,
  total,
  noun,
  onPageChange,
}: {
  page: number
  size: number
  total: number
  noun: string
  onPageChange: (page: number) => void
}) {
  const pages = Math.max(1, Math.ceil(total / size))
  const from = total === 0 ? 0 : (page - 1) * size + 1
  const to = Math.min(page * size, total)

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 px-1">
      <p className="text-sm text-muted-foreground" aria-live="polite">
        Mostrando {from} a {to} de {total} {noun}
      </p>
      <div className="flex items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          <ChevronLeftIcon data-icon="inline-start" />
          Anterior
        </Button>
        <Button
          variant="outline"
          size="sm"
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
        >
          Siguiente
          <ChevronRightIcon data-icon="inline-end" />
        </Button>
      </div>
    </div>
  )
}

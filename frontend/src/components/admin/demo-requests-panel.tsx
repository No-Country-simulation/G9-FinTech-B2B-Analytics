"use client"

import * as React from "react"
import Link from "next/link"
import {
  ChevronRightIcon,
  CircleAlertIcon,
  InboxIcon,
  SearchIcon,
  UserCheckIcon,
} from "lucide-react"

import { CreateUserButton } from "@/components/admin/create-user-button"
import { PageHeader } from "@/components/admin/page-header"
import { TablePagination } from "@/components/admin/table-pagination"
import { InitialsAvatar, ToneBadge, type Tone } from "@/components/admin/tone"
import { Alert, AlertAction, AlertDescription } from "@/components/ui/alert"
import { Button, buttonVariants } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  fetchAllPages,
  type AdminUser,
  type DemoRequest,
  type OrganizationType,
} from "@/lib/api"
import { useAuth } from "@/lib/auth"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"

const PAGE_SIZE = 10
const LAST_VISIT_KEY = "pricescope.admin.demo-requests.last-visit"

const ORGANIZATION_LABELS: Record<OrganizationType, string> = {
  fund: "Fondo",
  media: "Medio",
  retail: "Minorista",
  other: "Otro",
}

const ORGANIZATION_TONES: Record<OrganizationType, Tone> = {
  fund: "violet",
  media: "sky",
  retail: "emerald",
  other: "neutral",
}

const organizationItems = [
  { label: "Todas", value: "all" },
  ...Object.entries(ORGANIZATION_LABELS).map(([value, label]) => ({
    label,
    value,
  })),
]

// "New since the last visit" lives only in this browser (no backend state).
// Returns the previous visit and records the current one.
function swapLastVisit(): number | null {
  try {
    const previous = window.localStorage.getItem(LAST_VISIT_KEY)
    window.localStorage.setItem(LAST_VISIT_KEY, String(Date.now()))
    return previous ? Number(previous) : null
  } catch {
    return null
  }
}

export function DemoRequestsPanel() {
  const { request } = useAuth()
  const [requests, setRequests] = React.useState<DemoRequest[] | null>(null)
  const [error, setError] = React.useState<string | null>(null)
  const [lastVisit, setLastVisit] = React.useState<number | null>(null)
  const [search, setSearch] = React.useState("")
  const [organization, setOrganization] = React.useState("all")
  const [page, setPage] = React.useState(1)
  const [expanded, setExpanded] = React.useState<Set<string>>(new Set())

  // Requests whose email already has an account link to it instead of
  // offering to create a duplicate.
  const [userIdByEmail, setUserIdByEmail] = React.useState<Map<
    string,
    string
  > | null>(null)
  React.useEffect(() => {
    let ignore = false
    fetchAllPages<AdminUser>(request, "/admin/users")
      .then(
        (users) =>
          !ignore &&
          setUserIdByEmail(new Map(users.map((u) => [u.email, u.id])))
      )
      .catch(() => !ignore && setUserIdByEmail(new Map()))
    return () => {
      ignore = true
    }
  }, [request])

  // The endpoint has no search or filters, so we load every page and filter
  // here. It comes sorted newest first.
  const [reloadKey, setReloadKey] = React.useState(0)
  const visitRecorded = React.useRef(false)
  React.useEffect(() => {
    let ignore = false
    fetchAllPages<DemoRequest>(request, "/admin/demo-requests")
      .then((items) => {
        if (ignore) return
        // Recorded once per mount, so a second effect run (React Strict
        // Mode) or a retry does not read back the visit it just recorded.
        if (!visitRecorded.current) {
          visitRecorded.current = true
          setLastVisit(swapLastVisit())
        }
        setRequests(items)
      })
      .catch(() => !ignore && setError("No pudimos cargar las solicitudes."))
    return () => {
      ignore = true
    }
  }, [request, reloadKey])

  function retry() {
    setError(null)
    setRequests(null)
    setReloadKey((key) => key + 1)
  }

  const isNew = React.useCallback(
    (item: DemoRequest) =>
      lastVisit !== null && new Date(item.created_at).getTime() > lastVisit,
    [lastVisit]
  )

  const filtered = React.useMemo(() => {
    const term = search.trim().toLowerCase()
    return (requests ?? []).filter(
      (item) =>
        (organization === "all" || item.organization_type === organization) &&
        (!term ||
          item.company.toLowerCase().includes(term) ||
          item.email.toLowerCase().includes(term))
    )
  }, [requests, search, organization])

  const newCount = requests?.filter(isNew).length ?? 0
  const pageItems = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
  const hasFilters = search !== "" || organization !== "all"

  function clearFilters() {
    setSearch("")
    setOrganization("all")
    setPage(1)
  }

  function toggle(id: string) {
    setExpanded((current) => {
      const next = new Set(current)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  return (
    <>
      <PageHeader
        title="Solicitudes de demo"
        description="Personas que pidieron una demo desde el sitio. Contactalas y, después de la llamada, creá su usuario."
        badge={
          newCount > 0 && (
            <ToneBadge tone="brand">
              {newCount} {newCount === 1 ? "nueva" : "nuevas"} desde tu última
              visita
            </ToneBadge>
          )
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative w-full sm:w-72">
          <Label htmlFor="demo-search" className="sr-only">
            Buscar por empresa o correo
          </Label>
          <SearchIcon className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            id="demo-search"
            type="search"
            placeholder="Buscar por empresa o correo"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value)
              setPage(1)
            }}
            className="pl-8"
          />
        </div>
        <Label htmlFor="demo-organization" className="sr-only">
          Tipo de organización
        </Label>
        <Select
          items={organizationItems}
          value={organization}
          onValueChange={(value) => {
            setOrganization(value ?? "all")
            setPage(1)
          }}
        >
          <SelectTrigger id="demo-organization" className="w-44">
            <span className="text-muted-foreground">Organización:</span>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectGroup>
              {organizationItems.map((item) => (
                <SelectItem key={item.value} value={item.value}>
                  {item.label}
                </SelectItem>
              ))}
            </SelectGroup>
          </SelectContent>
        </Select>
      </div>

      {error ? (
        <Alert variant="destructive">
          <CircleAlertIcon />
          <AlertDescription>{error}</AlertDescription>
          <AlertAction>
            <Button size="xs" variant="outline" onClick={retry}>
              Reintentar
            </Button>
          </AlertAction>
        </Alert>
      ) : (
        <div className="overflow-hidden rounded-lg border">
          <Table>
            <TableHeader className="bg-muted">
              <TableRow>
                <TableHead className="w-10">
                  <span className="sr-only">Comentario</span>
                </TableHead>
                <TableHead>Empresa y contacto</TableHead>
                <TableHead>Correo</TableHead>
                <TableHead>Organización</TableHead>
                <TableHead>Preferencia</TableHead>
                <TableHead>Recibida</TableHead>
                <TableHead className="text-right">
                  <span className="sr-only">Acción</span>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {requests === null ? (
                <LoadingRows />
              ) : pageItems.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="h-40 text-center">
                    <EmptyState
                      filtered={hasFilters}
                      onClearFilters={clearFilters}
                    />
                  </TableCell>
                </TableRow>
              ) : (
                pageItems.map((item) => {
                  const open = expanded.has(item.id)
                  const commentId = `demo-comment-${item.id}`
                  return (
                    <React.Fragment key={item.id}>
                      <TableRow data-state={open ? "selected" : undefined}>
                        <TableCell>
                          <Button
                            variant="ghost"
                            size="icon-sm"
                            disabled={!item.comment}
                            onClick={() => toggle(item.id)}
                            aria-expanded={open}
                            aria-controls={commentId}
                            aria-label={
                              item.comment
                                ? open
                                  ? "Ocultar comentario"
                                  : "Ver comentario"
                                : "Sin comentario"
                            }
                          >
                            <ChevronRightIcon
                              className={cn(
                                "transition-transform",
                                open && "rotate-90"
                              )}
                            />
                          </Button>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-3">
                            <InitialsAvatar name={item.company} />
                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="font-medium">
                                  {item.company}
                                </span>
                                {isNew(item) && (
                                  <ToneBadge tone="brand">Nueva</ToneBadge>
                                )}
                              </div>
                              <div className="text-muted-foreground">
                                {item.name}
                              </div>
                            </div>
                          </div>
                        </TableCell>
                        <TableCell>
                          <a
                            href={`mailto:${item.email}`}
                            className="underline-offset-4 hover:underline"
                          >
                            {item.email}
                          </a>
                        </TableCell>
                        <TableCell>
                          <ToneBadge
                            tone={ORGANIZATION_TONES[item.organization_type]}
                          >
                            {ORGANIZATION_LABELS[item.organization_type]}
                          </ToneBadge>
                        </TableCell>
                        <TableCell className="tabular-nums">
                          {formatDateTime(item.preferred_date)}
                        </TableCell>
                        <TableCell className="text-muted-foreground tabular-nums">
                          {formatDateTime(item.created_at)}
                        </TableCell>
                        <TableCell className="text-right">
                          <RequestAction
                            item={item}
                            userId={userIdByEmail?.get(item.email.toLowerCase())}
                            loading={userIdByEmail === null}
                            onCreated={(user) =>
                              setUserIdByEmail((current) =>
                                new Map(current).set(user.email, user.id)
                              )
                            }
                          />
                        </TableCell>
                      </TableRow>
                      {open && item.comment && (
                        <TableRow id={commentId} className="bg-muted/30">
                          <TableCell />
                          <TableCell
                            colSpan={6}
                            className="py-3 whitespace-pre-wrap text-muted-foreground"
                          >
                            {item.comment}
                          </TableCell>
                        </TableRow>
                      )}
                    </React.Fragment>
                  )
                })
              )}
            </TableBody>
          </Table>
        </div>
      )}

      {requests !== null && !error && (
        <TablePagination
          page={page}
          size={PAGE_SIZE}
          total={filtered.length}
          noun={filtered.length === 1 ? "solicitud" : "solicitudes"}
          onPageChange={setPage}
        />
      )}
    </>
  )
}

function RequestAction({
  item,
  userId,
  loading,
  onCreated,
}: {
  item: DemoRequest
  userId: string | undefined
  loading: boolean
  onCreated: (user: AdminUser) => void
}) {
  if (loading) return <Skeleton className="ml-auto h-7 w-28" />
  if (userId) {
    return (
      <Link
        href={`/admin/usuarios/${userId}`}
        className={buttonVariants({ size: "sm", variant: "ghost" })}
      >
        <UserCheckIcon data-icon="inline-start" />
        Ver usuario
      </Link>
    )
  }
  return (
    <CreateUserButton
      size="sm"
      variant="outline"
      defaults={{ name: item.name, company: item.company, email: item.email }}
      onCreated={onCreated}
    />
  )
}

function LoadingRows() {
  return Array.from({ length: 5 }, (_, i) => (
    <TableRow key={i}>
      <TableCell colSpan={7}>
        <Skeleton className="h-8 w-full" />
      </TableCell>
    </TableRow>
  ))
}

function EmptyState({
  filtered,
  onClearFilters,
}: {
  filtered: boolean
  onClearFilters: () => void
}) {
  return (
    <div className="flex flex-col items-center gap-2 text-muted-foreground">
      <InboxIcon className="size-6" />
      {filtered ? (
        <>
          <p>Ninguna solicitud coincide con la búsqueda.</p>
          <Button variant="outline" size="sm" onClick={onClearFilters}>
            Limpiar filtros
          </Button>
        </>
      ) : (
        <p>Todavía no llegaron solicitudes de demo.</p>
      )}
    </div>
  )
}

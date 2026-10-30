"use client"

import * as React from "react"
import Link from "next/link"
import {
  BanIcon,
  CircleAlertIcon,
  DownloadIcon,
  EllipsisVerticalIcon,
  EyeIcon,
  LockOpenIcon,
  Loader2Icon,
  MailWarningIcon,
  SendIcon,
  SearchIcon,
  StoreIcon,
  UserCheckIcon,
  UserXIcon,
  UsersIcon,
} from "lucide-react"

import { CreateUserButton } from "@/components/admin/create-user-button"
import {
  AccountActionDialog,
  accountActionLabel,
  availableAccountActions,
  type AccountAction,
} from "@/components/admin/account-actions"
import { PageHeader } from "@/components/admin/page-header"
import { TablePagination } from "@/components/admin/table-pagination"
import {
  IconTile,
  InitialsAvatar,
  ToneBadge,
  type Tone,
} from "@/components/admin/tone"
import {
  ROLE_LABELS,
  RoleLabel,
  STATUS_LABELS,
  STATUS_TONES,
} from "@/components/admin/user-labels"
import { Alert, AlertAction, AlertDescription } from "@/components/ui/alert"
import { Button, buttonVariants } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Card,
  CardAction,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
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
import { toast } from "sonner"
import {
  ApiError,
  fetchAllPages,
  query,
  type AdminUser,
  type Page,
  type Role,
  type UserStatus,
} from "@/lib/api"
import { useAuth } from "@/lib/auth"
import { downloadCsv } from "@/lib/csv"
import { formatDate } from "@/lib/format"

const PAGE_SIZES = [10, 20, 50]
const SEARCH_DEBOUNCE_MS = 300

const roleItems = [
  { label: "Todos", value: "all" },
  { label: "Clientes", value: "client" },
  { label: "Admins", value: "admin" },
]

const pageSizeItems = PAGE_SIZES.map((size) => ({
  label: String(size),
  value: String(size),
}))

const statusItems = [
  { label: "Todos", value: "all" },
  ...Object.entries(STATUS_LABELS).map(([value, label]) => ({ label, value })),
]

type Kpis = {
  active: number
  pending: number
  withoutStores: number
  blockedOrDeactivated: number
}

export function UsersPanel() {
  const { request } = useAuth()
  const [search, setSearch] = React.useState("")
  const [debouncedSearch, setDebouncedSearch] = React.useState("")
  const [role, setRole] = React.useState<Role | "all">("all")
  const [status, setStatus] = React.useState<UserStatus | "all">("all")
  const [page, setPage] = React.useState(1)
  const [pageSize, setPageSize] = React.useState(PAGE_SIZES[0])
  const [selected, setSelected] = React.useState<Map<string, AdminUser>>(
    new Map()
  )
  const [exporting, setExporting] = React.useState(false)
  const [reloadKey, setReloadKey] = React.useState(0)
  // Each response is tagged with the query it answers, so a stale response
  // reads as "loading" without resetting state inside the effect.
  const [result, setResult] = React.useState<{
    path: string
    data?: Page<AdminUser>
    error?: string
  } | null>(null)

  React.useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search.trim())
      setPage(1)
    }, SEARCH_DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [search])

  const filters = {
    q: debouncedSearch,
    role: role === "all" ? null : role,
    status: status === "all" ? null : status,
  }
  const path = `/admin/users${query({ ...filters, page, size: pageSize })}`

  React.useEffect(() => {
    let ignore = false
    request<Page<AdminUser>>(path)
      .then((data) => !ignore && setResult({ path, data }))
      .catch(
        () =>
          !ignore &&
          setResult({ path, error: "No pudimos cargar los usuarios." })
      )
    return () => {
      ignore = true
    }
  }, [request, path, reloadKey])

  const current = result?.path === path ? result : null
  const data = current?.data ?? null
  const error = current?.error ?? null

  const hasFilters = search !== "" || role !== "all" || status !== "all"
  const pageIds = data?.items.map((user) => user.id) ?? []
  const selectedOnPage = pageIds.filter((id) => selected.has(id)).length
  const allOnPageSelected =
    pageIds.length > 0 && selectedOnPage === pageIds.length

  function clearFilters() {
    setSearch("")
    setDebouncedSearch("")
    setRole("all")
    setStatus("all")
    setPage(1)
  }

  function toggleUser(user: AdminUser, checked: boolean) {
    setSelected((current) => {
      const next = new Map(current)
      if (checked) next.set(user.id, user)
      else next.delete(user.id)
      return next
    })
  }

  function togglePage(checked: boolean) {
    setSelected((current) => {
      const next = new Map(current)
      for (const user of data?.items ?? []) {
        if (checked) next.set(user.id, user)
        else next.delete(user.id)
      }
      return next
    })
  }

  // Exports the selected users, or every user matching the filters.
  async function exportCsv() {
    setExporting(true)
    try {
      const users =
        selected.size > 0
          ? [...selected.values()]
          : await fetchAllPages<AdminUser>(request, "/admin/users", filters)
      downloadCsv(
        `usuarios-${new Date().toISOString().slice(0, 10)}.csv`,
        [
          "Nombre",
          "Correo",
          "Empresa",
          "Rol",
          "Estado",
          "Tiendas",
          "Último acceso",
          "Alta",
        ],
        users.map((user) => [
          user.name,
          user.email,
          user.company,
          ROLE_LABELS[user.role],
          STATUS_LABELS[user.status],
          user.role === "admin" ? "" : user.store_count,
          user.last_access_at ? formatDate(user.last_access_at) : "Nunca",
          formatDate(user.created_at),
        ])
      )
    } catch {
      toast.error("No pudimos exportar los usuarios.")
    } finally {
      setExporting(false)
    }
  }

  async function resendAccess(user: AdminUser) {
    try {
      const { message } = await request<{ message: string }>(
        `/admin/users/${user.id}/resend-access`,
        { method: "POST" }
      )
      toast.success(message, { description: user.email })
    } catch (err) {
      toast.error(
        err instanceof ApiError
          ? err.message
          : "No pudimos enviar el correo. Probá de nuevo."
      )
    }
  }

  return (
    <>
      <PageHeader
        title="Usuarios"
        description="Clientes y administradores con acceso a PriceScope."
      />

      <UserKpis refreshKey={reloadKey} />

      <Card className="gap-0 py-0 shadow-xs">
        <div className="grid gap-4 border-b p-(--card-spacing) sm:grid-cols-2">
          <FilterSelect
            id="users-role"
            label="Rol"
            items={roleItems}
            value={role}
            onChange={(value) => {
              setRole(value as Role | "all")
              setPage(1)
            }}
          />
          <FilterSelect
            id="users-status"
            label="Estado"
            items={statusItems}
            value={status}
            onChange={(value) => {
              setStatus(value as UserStatus | "all")
              setPage(1)
            }}
          />
        </div>

        <div className="flex flex-wrap items-center gap-2 border-b p-(--card-spacing)">
          <div className="relative w-full sm:w-72">
            <Label htmlFor="users-search" className="sr-only">
              Buscar por nombre o correo
            </Label>
            <SearchIcon className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              id="users-search"
              type="search"
              placeholder="Buscar por nombre o correo"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              className="h-9 pl-8"
            />
          </div>
          <div className="flex flex-wrap items-center gap-2 sm:ml-auto">
            <Label htmlFor="users-page-size" className="sr-only">
              Filas por página
            </Label>
            <Select
              items={pageSizeItems}
              value={String(pageSize)}
              onValueChange={(value) => {
                setPageSize(Number(value))
                setPage(1)
              }}
            >
              <SelectTrigger id="users-page-size" className="h-9! w-20">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {pageSizeItems.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              size="lg"
              onClick={exportCsv}
              disabled={exporting}
            >
              {exporting ? (
                <Loader2Icon className="animate-spin" data-icon="inline-start" />
              ) : (
                <DownloadIcon data-icon="inline-start" />
              )}
              {selected.size > 0 ? `Exportar (${selected.size})` : "Exportar"}
            </Button>
            <CreateUserButton
              size="lg"
              onCreated={() => setReloadKey((key) => key + 1)}
            />
          </div>
        </div>

        {error ? (
          <div className="p-(--card-spacing)">
            <Alert variant="destructive">
              <CircleAlertIcon />
              <AlertDescription>{error}</AlertDescription>
              <AlertAction>
                <Button
                  size="xs"
                  variant="outline"
                  onClick={() => {
                    setResult(null)
                    setReloadKey((key) => key + 1)
                  }}
                >
                  Reintentar
                </Button>
              </AlertAction>
            </Alert>
          </div>
        ) : (
          <Table>
            <TableHeader className="bg-muted/50">
              <TableRow>
                <TableHead className="w-12 pl-(--card-spacing)">
                  <Checkbox
                    checked={allOnPageSelected}
                    indeterminate={selectedOnPage > 0 && !allOnPageSelected}
                    onCheckedChange={(checked) => togglePage(checked)}
                    disabled={pageIds.length === 0}
                    aria-label="Seleccionar los usuarios de esta página"
                  />
                </TableHead>
                <TableHead>Usuario</TableHead>
                <TableHead>Empresa</TableHead>
                <TableHead>Rol</TableHead>
                <TableHead>Estado</TableHead>
                <TableHead>Tiendas</TableHead>
                <TableHead>Último acceso</TableHead>
                <TableHead className="pr-(--card-spacing) text-right">
                  Acciones
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data === null ? (
                Array.from({ length: 5 }, (_, i) => (
                  <TableRow key={i}>
                    <TableCell colSpan={8} className="px-(--card-spacing)">
                      <Skeleton className="h-9 w-full" />
                    </TableCell>
                  </TableRow>
                ))
              ) : data.items.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={8} className="h-40 text-center">
                    <div className="flex flex-col items-center gap-2 text-muted-foreground">
                      <UsersIcon className="size-6" />
                      {hasFilters ? (
                        <>
                          <p>Ningún usuario coincide con la búsqueda.</p>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={clearFilters}
                          >
                            Limpiar filtros
                          </Button>
                        </>
                      ) : (
                        <p>Todavía no hay usuarios.</p>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ) : (
                data.items.map((user) => (
                  <TableRow
                    key={user.id}
                    data-state={selected.has(user.id) ? "selected" : undefined}
                    className="even:bg-muted/40 data-[state=selected]:bg-brand/8 dark:data-[state=selected]:bg-brand/15"
                  >
                    <TableCell className="pl-(--card-spacing)">
                      <Checkbox
                        checked={selected.has(user.id)}
                        onCheckedChange={(checked) => toggleUser(user, checked)}
                        aria-label={`Seleccionar a ${user.name}`}
                      />
                    </TableCell>
                    <TableCell className="py-3">
                      <div className="flex items-center gap-3">
                        <InitialsAvatar name={user.name} className="size-10" />
                        <div className="min-w-0">
                          <Link
                            href={`/admin/usuarios/${user.id}`}
                            className="font-medium underline-offset-4 hover:underline"
                          >
                            {user.name}
                          </Link>
                          <div className="text-muted-foreground">
                            {user.email}
                          </div>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{user.company}</TableCell>
                    <TableCell>
                      <RoleLabel role={user.role} />
                    </TableCell>
                    <TableCell>
                      <ToneBadge tone={STATUS_TONES[user.status]}>
                        {STATUS_LABELS[user.status]}
                      </ToneBadge>
                    </TableCell>
                    <TableCell>
                      <StoreCount user={user} />
                    </TableCell>
                    <TableCell className="text-muted-foreground tabular-nums">
                      {user.last_access_at
                        ? formatDate(user.last_access_at)
                        : "Nunca"}
                    </TableCell>
                    <TableCell className="pr-(--card-spacing)">
                      <UserActions
                        user={user}
                        onResendAccess={resendAccess}
                        onAccountChange={() =>
                          setReloadKey((key) => key + 1)
                        }
                      />
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        )}

        {data !== null && !error && (
          <div className="border-t p-(--card-spacing)">
            <TablePagination
              page={page}
              size={pageSize}
              total={data.total}
              noun={data.total === 1 ? "usuario" : "usuarios"}
              onPageChange={setPage}
            />
          </div>
        )}
      </Card>
    </>
  )
}

function FilterSelect({
  id,
  label,
  items,
  value,
  onChange,
}: {
  id: string
  label: string
  items: { label: string; value: string }[]
  value: string
  onChange: (value: string) => void
}) {
  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <Select
        items={items}
        value={value}
        onValueChange={(next) => onChange(next ?? "all")}
      >
        <SelectTrigger id={id} className="h-9! w-full">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectGroup>
            {items.map((item) => (
              <SelectItem key={item.value} value={item.value}>
                {item.label}
              </SelectItem>
            ))}
          </SelectGroup>
        </SelectContent>
      </Select>
    </div>
  )
}

function UserActions({
  user,
  onResendAccess,
  onAccountChange,
}: {
  user: AdminUser
  onResendAccess: (user: AdminUser) => void
  onAccountChange: () => void
}) {
  const { user: me } = useAuth()
  const [action, setAction] = React.useState<AccountAction | null>(null)
  const actions = availableAccountActions(user, me?.id)

  return (
    <div className="flex items-center justify-end gap-1">
      <Link
        href={`/admin/usuarios/${user.id}`}
        className={buttonVariants({ variant: "ghost", size: "icon-sm" })}
        aria-label={`Ver a ${user.name}`}
      >
        <EyeIcon />
      </Link>
      <DropdownMenu>
        <DropdownMenuTrigger
          render={
            <Button
              variant="ghost"
              size="icon-sm"
              className="data-open:bg-muted"
              aria-label={`Más acciones para ${user.name}`}
            />
          }
        >
          <EllipsisVerticalIcon />
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="min-w-56">
          <DropdownMenuItem
            disabled={user.status !== "pending"}
            onClick={() => onResendAccess(user)}
          >
            <SendIcon />
            Reenviar correo de acceso
          </DropdownMenuItem>
          {actions.length > 0 && <DropdownMenuSeparator />}
          {actions.map((item) => (
            <DropdownMenuItem
              key={item}
              variant={item === "unblock" ? "default" : "destructive"}
              onClick={() => setAction(item)}
            >
              {item === "block" && <BanIcon />}
              {item === "unblock" && <LockOpenIcon />}
              {item === "deactivate" && <UserXIcon />}
              {accountActionLabel(item)}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
      <AccountActionDialog
        user={user}
        action={action}
        onClose={() => setAction(null)}
        onDone={onAccountChange}
      />
    </div>
  )
}

function StoreCount({ user }: { user: AdminUser }) {
  if (user.role === "admin") {
    return <span className="text-muted-foreground">—</span>
  }
  if (user.store_count === 0) {
    return <ToneBadge tone="amber">Sin tiendas</ToneBadge>
  }
  return (
    <span className="tabular-nums">
      {user.store_count} {user.store_count === 1 ? "tienda" : "tiendas"}
    </span>
  )
}

function UserKpis({ refreshKey }: { refreshKey: number }) {
  const { request } = useAuth()
  const [kpis, setKpis] = React.useState<Kpis | null>(null)
  const [failed, setFailed] = React.useState(false)

  // The API has no aggregate endpoint for these yet, so they are counted from
  // the full user list. Move to the backend if the list grows large.
  React.useEffect(() => {
    let ignore = false
    fetchAllPages<AdminUser>(request, "/admin/users")
      .then((users) => {
        if (ignore) return
        const count = (match: (u: AdminUser) => boolean) =>
          users.filter(match).length
        setKpis({
          active: count((u) => u.status === "active"),
          pending: count((u) => u.status === "pending"),
          withoutStores: count(
            (u) =>
              u.role === "client" &&
              (u.status === "active" || u.status === "pending") &&
              u.store_count === 0
          ),
          blockedOrDeactivated: count(
            (u) => u.status === "blocked" || u.status === "deactivated"
          ),
        })
      })
      .catch(() => !ignore && setFailed(true))
    return () => {
      ignore = true
    }
  }, [request, refreshKey])

  const cards: {
    label: string
    value?: number
    hint: string
    tone: Tone
    icon: React.ReactNode
  }[] = [
    {
      label: "Activos",
      value: kpis?.active,
      hint: "Ya ingresaron y pueden usar la plataforma",
      tone: "emerald",
      icon: <UserCheckIcon />,
    },
    {
      label: "Pendientes de contraseña",
      value: kpis?.pending,
      hint: "Recibieron el correo pero no crearon su contraseña",
      tone: "amber",
      icon: <MailWarningIcon />,
    },
    {
      label: "Sin tiendas asignadas",
      value: kpis?.withoutStores,
      hint: "Clientes que todavía no ven datos",
      tone: "brand",
      icon: <StoreIcon />,
    },
    {
      label: "Bloqueados o de baja",
      value: kpis?.blockedOrDeactivated,
      hint: "Sin acceso a la plataforma",
      tone: "red",
      icon: <UserXIcon />,
    },
  ]

  return (
    <div className="grid grid-cols-1 gap-4 @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.label} className="@container/card shadow-xs">
          <CardHeader>
            <CardDescription>{card.label}</CardDescription>
            <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
              {card.value !== undefined ? (
                card.value
              ) : failed ? (
                <span className="text-muted-foreground">—</span>
              ) : (
                <Skeleton className="h-8 w-16" />
              )}
            </CardTitle>
            <CardAction>
              <IconTile tone={card.tone}>{card.icon}</IconTile>
            </CardAction>
            <p className="col-span-full pt-1 text-sm text-muted-foreground">
              {card.hint}
            </p>
          </CardHeader>
        </Card>
      ))}
    </div>
  )
}

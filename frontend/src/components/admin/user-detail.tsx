"use client"

import * as React from "react"
import Link from "next/link"
import {
  ArrowLeftIcon,
  BanIcon,
  KeyRoundIcon,
  LockOpenIcon,
  CircleAlertIcon,
  ClockIcon,
  ExternalLinkIcon,
  Loader2Icon,
  SendIcon,
  StoreIcon,
  TriangleAlertIcon,
  UserXIcon,
} from "lucide-react"
import { toast } from "sonner"

import {
  AccountActionDialog,
  accountActionLabel,
  availableAccountActions,
  type AccountAction,
} from "@/components/admin/account-actions"
import { IconTile, InitialsAvatar, ToneBadge } from "@/components/admin/tone"
import {
  RoleLabel,
  STATUS_LABELS,
  STATUS_TONES,
  STORE_CATEGORY_LABELS,
} from "@/components/admin/user-labels"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button, buttonVariants } from "@/components/ui/button"
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
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
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ApiError, type AdminUser, type Store } from "@/lib/api"
import { useAuth } from "@/lib/auth"
import { formatDate, formatShortDate } from "@/lib/format"

type Loaded = {
  user: AdminUser
  stores: Store[]
  // Active stores of the catalog; only loaded for clients.
  catalog: Store[]
}

export function UserDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = React.use(params)
  const { request } = useAuth()
  const [result, setResult] = React.useState<{
    id: string
    data?: Loaded
    error?: "not-found" | "failed"
  } | null>(null)
  const [reloadKey, setReloadKey] = React.useState(0)

  React.useEffect(() => {
    let ignore = false
    async function load(): Promise<Loaded> {
      const user = await request<AdminUser>(`/admin/users/${id}`)
      if (user.role === "admin") return { user, stores: [], catalog: [] }
      const [stores, catalog] = await Promise.all([
        request<Store[]>(`/admin/users/${id}/stores`),
        request<Store[]>("/admin/stores"),
      ])
      return { user, stores, catalog: catalog.filter((s) => s.active) }
    }
    load()
      .then((data) => !ignore && setResult({ id, data }))
      .catch((err) => {
        if (ignore) return
        const notFound =
          err instanceof ApiError && (err.status === 404 || err.status === 422)
        setResult({ id, error: notFound ? "not-found" : "failed" })
      })
    return () => {
      ignore = true
    }
  }, [request, id, reloadKey])

  const current = result?.id === id ? result : null

  // Store changes come back from the API; keep the counter in sync with them.
  const setStores = React.useCallback((stores: Store[]) => {
    setResult((prev) =>
      prev?.data
        ? {
            ...prev,
            data: {
              ...prev.data,
              stores,
              user: { ...prev.data.user, store_count: stores.length },
            },
          }
        : prev
    )
  }, [])

  const setUser = React.useCallback((user: AdminUser) => {
    setResult((prev) =>
      prev?.data ? { ...prev, data: { ...prev.data, user } } : prev
    )
  }, [])

  return (
    <>
      <Link
        href="/admin/usuarios"
        className={buttonVariants({
          variant: "ghost",
          size: "sm",
          className: "-ml-2 w-fit text-muted-foreground",
        })}
      >
        <ArrowLeftIcon data-icon="inline-start" />
        Usuarios
      </Link>

      {current?.error === "not-found" ? (
        <Alert>
          <UserXIcon />
          <AlertDescription>
            No encontramos este usuario. Puede que el enlace esté mal escrito.
          </AlertDescription>
        </Alert>
      ) : current?.error ? (
        <Alert variant="destructive">
          <CircleAlertIcon />
          <AlertDescription>No pudimos cargar el usuario.</AlertDescription>
          <Button
            size="xs"
            variant="outline"
            className="col-start-2 mt-2 w-fit"
            onClick={() => {
              setResult(null)
              setReloadKey((key) => key + 1)
            }}
          >
            Reintentar
          </Button>
        </Alert>
      ) : current?.data ? (
        <div className="grid items-start gap-4 lg:grid-cols-[340px_1fr]">
          <ProfileCard user={current.data.user} onUserChange={setUser} />
          <Tabs defaultValue="stores" className="min-w-0 gap-4">
            <TabsList>
              <TabsTrigger value="stores">
                <StoreIcon />
                Tiendas
              </TabsTrigger>
              <TabsTrigger value="access">
                <KeyRoundIcon />
                Acceso
              </TabsTrigger>
            </TabsList>
            <TabsContent value="stores">
              <StoresCard
                user={current.data.user}
                stores={current.data.stores}
                catalog={current.data.catalog}
                onStoresChange={setStores}
              />
            </TabsContent>
            <TabsContent value="access" className="flex flex-col gap-4">
              <EmailCard user={current.data.user} onUserChange={setUser} />
              <PasswordCard user={current.data.user} />
            </TabsContent>
          </Tabs>
        </div>
      ) : (
        <UserDetailSkeleton />
      )}
    </>
  )
}

export function UserDetailSkeleton() {
  return (
    <div className="grid items-start gap-4 lg:grid-cols-[340px_1fr]">
      <Skeleton className="h-[460px] rounded-xl" />
      <Skeleton className="h-[320px] rounded-xl" />
    </div>
  )
}

function ProfileCard({
  user,
  onUserChange,
}: {
  user: AdminUser
  onUserChange: (user: AdminUser) => void
}) {
  const { user: me } = useAuth()
  const [action, setAction] = React.useState<AccountAction | null>(null)
  const isClient = user.role === "client"
  const actions = availableAccountActions(user, me?.id)

  return (
    <Card className="shadow-xs">
      <CardContent className="flex flex-col items-center gap-3 pt-2 text-center">
        <InitialsAvatar name={user.name} size="lg" />
        <div className="flex flex-col gap-1">
          <h2 className="text-lg font-semibold tracking-tight">{user.name}</h2>
          <p className="text-sm break-all text-muted-foreground">
            {user.email}
          </p>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <RoleLabel role={user.role} />
          <ToneBadge tone={STATUS_TONES[user.status]}>
            {STATUS_LABELS[user.status]}
          </ToneBadge>
        </div>
      </CardContent>

      <CardContent className="grid grid-cols-2 gap-3">
        <Stat
          tone="brand"
          icon={<StoreIcon />}
          value={isClient ? String(user.store_count) : "—"}
          label={user.store_count === 1 ? "Tienda" : "Tiendas"}
        />
        <Stat
          tone="emerald"
          icon={<ClockIcon />}
          value={
            user.last_access_at ? formatShortDate(user.last_access_at) : "Nunca"
          }
          label="Último acceso"
        />
      </CardContent>

      <CardContent className="flex flex-col gap-3">
        <Separator />
        <h3 className="text-sm font-semibold">Datos</h3>
        <dl className="grid grid-cols-[110px_1fr] gap-x-3 gap-y-2.5 text-sm">
          <dt className="text-muted-foreground">Empresa</dt>
          <dd>{user.company}</dd>
          <dt className="text-muted-foreground">Alta</dt>
          <dd className="tabular-nums">{formatDate(user.created_at)}</dd>
          <dt className="text-muted-foreground">Contraseña</dt>
          <dd>
            {user.status === "pending"
              ? "Todavía no la definió"
              : user.status === "active"
                ? "Definida"
                : "—"}
          </dd>
        </dl>
      </CardContent>

      {user.status === "deactivated" ? (
        <CardFooter className="text-sm text-muted-foreground">
          Cuenta dada de baja: no puede volver a ingresar.
        </CardFooter>
      ) : user.id === me?.id ? (
        <CardFooter className="text-sm text-muted-foreground">
          Es tu cuenta: no podés bloquearla ni darla de baja desde acá.
        </CardFooter>
      ) : (
        actions.length > 0 && (
          <CardFooter className="grid grid-cols-2 gap-2">
            {actions.map((item) => (
              <Button
                key={item}
                variant="outline"
                className={
                  item === "unblock"
                    ? undefined
                    : "text-destructive hover:bg-destructive/10 hover:text-destructive"
                }
                onClick={() => setAction(item)}
              >
                {item === "block" && <BanIcon data-icon="inline-start" />}
                {item === "unblock" && (
                  <LockOpenIcon data-icon="inline-start" />
                )}
                {item === "deactivate" && (
                  <UserXIcon data-icon="inline-start" />
                )}
                {accountActionLabel(item)}
              </Button>
            ))}
          </CardFooter>
        )
      )}
      <AccountActionDialog
        user={user}
        action={action}
        onClose={() => setAction(null)}
        onDone={onUserChange}
      />
    </Card>
  )
}

function Stat({
  tone,
  icon,
  value,
  label,
}: {
  tone: "brand" | "emerald"
  icon: React.ReactNode
  value: string
  label: string
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border p-3">
      <IconTile tone={tone}>{icon}</IconTile>
      <div className="flex min-w-0 flex-col text-left">
        <span className="truncate font-semibold tabular-nums">{value}</span>
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
    </div>
  )
}

function domainOf(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, "")
  } catch {
    return url
  }
}

function StoresCard({
  user,
  stores,
  catalog,
  onStoresChange,
}: {
  user: AdminUser
  stores: Store[]
  catalog: Store[]
  onStoresChange: (stores: Store[]) => void
}) {
  const { request } = useAuth()
  const [pick, setPick] = React.useState<string | null>(null)
  const [assigning, setAssigning] = React.useState(false)
  const [toRemove, setToRemove] = React.useState<Store | null>(null)
  const [removing, setRemoving] = React.useState(false)

  const assignedIds = new Set(stores.map((store) => store.id))
  const available = catalog.filter((store) => !assignedIds.has(store.id))
  const availableItems = available.map((store) => ({
    label: store.name,
    value: store.id,
  }))

  async function assign() {
    if (!pick) return
    setAssigning(true)
    try {
      const updated = await request<Store[]>(
        `/admin/users/${user.id}/stores`,
        { method: "POST", body: JSON.stringify({ store_id: pick }) }
      )
      const name = available.find((store) => store.id === pick)?.name
      onStoresChange(updated)
      setPick(null)
      toast.success(`Asignaste ${name} a ${user.name}.`)
    } catch (err) {
      toast.error(
        err instanceof ApiError ? err.message : "No pudimos asignar la tienda."
      )
    } finally {
      setAssigning(false)
    }
  }

  async function remove() {
    if (!toRemove) return
    setRemoving(true)
    try {
      await request<void>(`/admin/users/${user.id}/stores/${toRemove.id}`, {
        method: "DELETE",
      })
      onStoresChange(stores.filter((store) => store.id !== toRemove.id))
      toast.success(`Quitaste ${toRemove.name}.`)
      setToRemove(null)
    } catch (err) {
      toast.error(
        err instanceof ApiError ? err.message : "No pudimos quitar la tienda."
      )
    } finally {
      setRemoving(false)
    }
  }

  if (user.role === "admin") {
    return (
      <Card className="shadow-xs">
        <CardHeader>
          <CardTitle>Tiendas asignadas</CardTitle>
          <CardDescription>
            Las tiendas solo se asignan a clientes.
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  return (
    <Card className="gap-0 py-0 shadow-xs">
      <CardHeader className="border-b py-(--card-spacing)">
        <CardTitle>Tiendas asignadas</CardTitle>
        <CardDescription>
          El cliente solo ve precios de estas tiendas en el dashboard, la
          matriz y las alertas.
        </CardDescription>
        <CardAction className="col-span-full col-start-1 row-start-3 mt-3 flex flex-wrap items-center gap-2 justify-self-start sm:col-span-1 sm:col-start-2 sm:row-start-1 sm:mt-0 sm:justify-self-end">
          <Label htmlFor="assign-store" className="sr-only">
            Tienda para asignar
          </Label>
          <Select
            items={availableItems}
            value={pick}
            onValueChange={(value) => setPick(value)}
            disabled={available.length === 0}
          >
            <SelectTrigger id="assign-store" className="h-9! w-56">
              <SelectValue
                placeholder={
                  available.length === 0
                    ? "No hay más tiendas"
                    : "Elegí una tienda…"
                }
              />
            </SelectTrigger>
            <SelectContent>
              <SelectGroup>
                {availableItems.map((item) => (
                  <SelectItem key={item.value} value={item.value}>
                    {item.label}
                  </SelectItem>
                ))}
              </SelectGroup>
            </SelectContent>
          </Select>
          <Button size="lg" onClick={assign} disabled={!pick || assigning}>
            {assigning && (
              <Loader2Icon className="animate-spin" data-icon="inline-start" />
            )}
            Asignar
          </Button>
        </CardAction>
      </CardHeader>

      {stores.length === 0 ? (
        <div className="flex flex-col items-center gap-2 px-6 py-12 text-center">
          <IconTile tone="amber">
            <StoreIcon />
          </IconTile>
          <p className="font-semibold">Sin tiendas asignadas</p>
          <p className="max-w-sm text-sm text-muted-foreground">
            El cliente ve el tablero vacío hasta que le asignes al menos una
            tienda.
          </p>
        </div>
      ) : (
        <ul className="divide-y">
          {stores.map((store) => (
            <li
              key={store.id}
              className="flex items-center gap-3 px-(--card-spacing) py-3.5"
            >
              <InitialsAvatar
                name={store.name}
                className="size-10 rounded-lg after:rounded-lg *:rounded-lg"
              />
              <div className="flex min-w-0 flex-1 flex-col">
                <span className="font-medium">{store.name}</span>
                <span className="flex items-center gap-1.5 text-sm text-muted-foreground">
                  {STORE_CATEGORY_LABELS[store.category]}
                  <span aria-hidden="true">·</span>
                  <a
                    href={store.base_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 underline-offset-4 hover:text-foreground hover:underline"
                  >
                    {domainOf(store.base_url)}
                    <ExternalLinkIcon className="size-3" />
                  </a>
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="text-destructive hover:bg-destructive/10 hover:text-destructive"
                onClick={() => setToRemove(store)}
              >
                Quitar
              </Button>
            </li>
          ))}
        </ul>
      )}

      <Dialog
        open={toRemove !== null}
        onOpenChange={(open) => !open && !removing && setToRemove(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>¿Quitar {toRemove?.name}?</DialogTitle>
            <DialogDescription>
              {user.name} dejará de ver los precios de esta tienda.
            </DialogDescription>
          </DialogHeader>
          {stores.length === 1 && (
            <Alert className="border-amber-500/30 bg-amber-500/10 text-amber-800 dark:text-amber-300">
              <TriangleAlertIcon />
              <AlertDescription className="text-current">
                Es la última tienda: el cliente dejará de ver datos.
              </AlertDescription>
            </Alert>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setToRemove(null)}
              disabled={removing}
            >
              Cancelar
            </Button>
            <Button
              className="bg-destructive text-white hover:bg-destructive/90"
              onClick={remove}
              disabled={removing}
            >
              {removing && (
                <Loader2Icon className="animate-spin" data-icon="inline-start" />
              )}
              Quitar tienda
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  )
}

function EmailCard({
  user,
  onUserChange,
}: {
  user: AdminUser
  onUserChange: (user: AdminUser) => void
}) {
  const { request } = useAuth()
  const [email, setEmail] = React.useState("")
  const [saving, setSaving] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const editable = user.status === "active" || user.status === "pending"
  const unchanged =
    email.trim().toLowerCase() === "" ||
    email.trim().toLowerCase() === user.email

  async function save(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const result = await request<{ user: AdminUser; email_queued: boolean }>(
        `/admin/users/${user.id}/email`,
        { method: "PATCH", body: JSON.stringify({ email: email.trim() }) }
      )
      onUserChange(result.user)
      setEmail("")
      toast.success("Cambiaste el correo.", {
        description: result.email_queued
          ? `Le reenviamos el correo de acceso a ${result.user.email}.`
          : `Ahora ingresa con ${result.user.email}.`,
      })
    } catch (err) {
      setError(
        err instanceof ApiError && err.status < 500 && err.status !== 422
          ? err.message
          : err instanceof ApiError && err.status === 422
            ? "Escribí un correo válido."
            : "No pudimos cambiar el correo. Probá de nuevo."
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card className="shadow-xs">
      <CardHeader>
        <CardTitle>Correo de acceso</CardTitle>
        <CardDescription>
          {user.status === "pending"
            ? "Si lo cambiás, le reenviamos el correo de acceso a la dirección nueva."
            : "Es el correo con el que ingresa. Los enlaces enviados a la dirección anterior dejan de funcionar."}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {editable ? (
          <form onSubmit={save} className="flex flex-col gap-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="flex flex-col gap-2">
                <Label htmlFor="current-email">Correo actual</Label>
                <Input
                  id="current-email"
                  value={user.email}
                  readOnly
                  className="h-9 bg-muted/50"
                />
              </div>
              <div className="flex flex-col gap-2">
                <Label htmlFor="new-email">Correo nuevo</Label>
                <Input
                  id="new-email"
                  type="email"
                  placeholder="nombre@empresa.com"
                  value={email}
                  onChange={(event) => {
                    setEmail(event.target.value)
                    setError(null)
                  }}
                  aria-invalid={error ? true : undefined}
                  aria-describedby={error ? "new-email-error" : undefined}
                  required
                  className="h-9"
                />
              </div>
            </div>
            {error && (
              <p id="new-email-error" role="alert" className="text-sm text-destructive">
                {error}
              </p>
            )}
            <Button
              type="submit"
              size="lg"
              className="w-fit"
              disabled={unchanged || saving}
            >
              {saving && (
                <Loader2Icon className="animate-spin" data-icon="inline-start" />
              )}
              Cambiar correo
            </Button>
          </form>
        ) : (
          <p className="text-sm text-muted-foreground">
            {user.status === "blocked"
              ? "Desbloqueá la cuenta para cambiar el correo."
              : "La cuenta está dada de baja."}
          </p>
        )}
      </CardContent>
    </Card>
  )
}

function PasswordCard({ user }: { user: AdminUser }) {
  const { request } = useAuth()
  const [sending, setSending] = React.useState(false)

  // Active users get a reset link; pending users have not set a password yet,
  // so they get the access email again.
  const path =
    user.status === "active"
      ? `/admin/users/${user.id}/password-reset`
      : `/admin/users/${user.id}/resend-access`

  async function send() {
    setSending(true)
    try {
      const { message } = await request<{ message: string }>(path, {
        method: "POST",
      })
      toast.success(message, { description: user.email })
    } catch (err) {
      toast.error(
        err instanceof ApiError
          ? err.message
          : "No pudimos enviar el correo. Probá de nuevo."
      )
    } finally {
      setSending(false)
    }
  }

  const description = {
    active:
      "Le enviamos un enlace para que defina una contraseña nueva. Nunca ves ni escribís su contraseña.",
    pending:
      "Todavía no definió su contraseña. Si el enlace venció o no le llegó, reenvialo.",
    blocked: "Desbloqueá la cuenta para gestionar la contraseña.",
    deactivated: "La cuenta está dada de baja.",
  }[user.status]

  return (
    <Card className="shadow-xs">
      <CardHeader>
        <CardTitle>Contraseña</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      {(user.status === "active" || user.status === "pending") && (
        <CardContent>
          <Button size="lg" variant="outline" onClick={send} disabled={sending}>
            {sending ? (
              <Loader2Icon className="animate-spin" data-icon="inline-start" />
            ) : (
              <SendIcon data-icon="inline-start" />
            )}
            {user.status === "active"
              ? "Enviar enlace para restablecer"
              : "Reenviar correo de acceso"}
          </Button>
        </CardContent>
      )}
    </Card>
  )
}

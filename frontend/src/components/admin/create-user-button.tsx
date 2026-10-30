"use client"

import * as React from "react"
import { useRouter } from "next/navigation"
import { Loader2Icon, UserPlusIcon } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
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
import { ApiError, type AdminUser, type Role } from "@/lib/api"
import { useAuth } from "@/lib/auth"

export type NewUserDefaults = {
  name?: string
  company?: string
  email?: string
}

type Field = "name" | "company" | "email"
type Errors = Partial<Record<Field, string>>

const roleItems = [
  { label: "Cliente", value: "client" },
  { label: "Admin", value: "admin" },
]

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

// Mirrors the backend limits (UserCreate) so most mistakes are caught here,
// with Spanish messages, before the request.
function validate(values: Record<Field, string>): Errors {
  const errors: Errors = {}
  if (values.name.length < 2) errors.name = "Escribí el nombre y apellido."
  else if (values.name.length > 120) errors.name = "Usá hasta 120 caracteres."
  if (values.company.length < 2) errors.company = "Escribí el nombre de la empresa."
  else if (values.company.length > 160)
    errors.company = "Usá hasta 160 caracteres."
  if (!EMAIL_PATTERN.test(values.email)) errors.email = "Escribí un correo válido."
  return errors
}

export function CreateUserButton({
  size = "default",
  variant = "default",
  defaults,
  onCreated,
}: {
  size?: "default" | "sm" | "lg"
  variant?: "default" | "outline"
  defaults?: NewUserDefaults
  onCreated?: (user: AdminUser) => void
}) {
  const [open, setOpen] = React.useState(false)

  return (
    <>
      <Button size={size} variant={variant} onClick={() => setOpen(true)}>
        <UserPlusIcon data-icon="inline-start" />
        Crear usuario
      </Button>
      <CreateUserDialog
        open={open}
        onOpenChange={setOpen}
        defaults={defaults}
        onCreated={onCreated}
      />
    </>
  )
}

function CreateUserDialog({
  open,
  onOpenChange,
  defaults,
  onCreated,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  defaults?: NewUserDefaults
  onCreated?: (user: AdminUser) => void
}) {
  const router = useRouter()
  const { request } = useAuth()
  const [role, setRole] = React.useState<Role>("client")
  const [errors, setErrors] = React.useState<Errors>({})
  const [formError, setFormError] = React.useState<string | null>(null)
  const [saving, setSaving] = React.useState(false)

  function close() {
    if (saving) return
    onOpenChange(false)
    setErrors({})
    setFormError(null)
    setRole("client")
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const values = {
      name: String(form.get("name") ?? "").trim(),
      company: String(form.get("company") ?? "").trim(),
      email: String(form.get("email") ?? "").trim(),
    }
    const found = validate(values)
    setErrors(found)
    setFormError(null)
    if (Object.keys(found).length > 0) return

    setSaving(true)
    try {
      const result = await request<{ user: AdminUser; email_queued: boolean }>(
        "/admin/users",
        { method: "POST", body: JSON.stringify({ ...values, role }) }
      )
      const created = result.user
      const goToUser = {
        label: "Ver usuario",
        onClick: () => router.push(`/admin/usuarios/${created.id}`),
      }
      if (result.email_queued) {
        toast.success(`Creaste a ${created.name}.`, {
          description: `Le enviamos el correo de acceso a ${created.email}.`,
          action: goToUser,
        })
      } else {
        toast.warning(`Creaste a ${created.name}, pero no salió el correo.`, {
          description: "Reenvialo desde su perfil en unos minutos.",
          action: goToUser,
        })
      }
      onCreated?.(created)
      setSaving(false)
      close()
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setErrors({ email: err.message })
      } else if (err instanceof ApiError && err.status === 422) {
        setFormError("Revisá los datos: alguno no tiene el formato esperado.")
      } else {
        setFormError(
          err instanceof ApiError && err.status < 500
            ? err.message
            : "No pudimos crear el usuario. Probá de nuevo."
        )
      }
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !next && close()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Crear usuario</DialogTitle>
          <DialogDescription>
            Le enviamos un correo para que defina su contraseña. Hasta entonces
            queda pendiente.
          </DialogDescription>
        </DialogHeader>
        <form
          id="create-user-form"
          onSubmit={submit}
          noValidate
          className="flex flex-col gap-4"
        >
          <TextField
            name="name"
            label="Nombre y apellido"
            placeholder="Valeria Luna"
            autoComplete="name"
            defaultValue={defaults?.name}
            error={errors.name}
          />
          <TextField
            name="company"
            label="Empresa"
            placeholder="Sol Mayorista"
            autoComplete="organization"
            defaultValue={defaults?.company}
            error={errors.company}
          />
          <TextField
            name="email"
            label="Correo"
            type="email"
            placeholder="nombre@empresa.com"
            autoComplete="email"
            defaultValue={defaults?.email}
            error={errors.email}
          />
          <div className="flex flex-col gap-2">
            <Label htmlFor="new-user-role">Rol</Label>
            <Select
              items={roleItems}
              value={role}
              onValueChange={(value) => setRole((value ?? "client") as Role)}
            >
              <SelectTrigger id="new-user-role" className="h-9! w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectGroup>
                  {roleItems.map((item) => (
                    <SelectItem key={item.value} value={item.value}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectGroup>
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              {role === "client"
                ? "Ve el dashboard con las tiendas que le asignes."
                : "Tiene acceso completo a este backoffice."}
            </p>
          </div>
          {formError && (
            <p role="alert" className="text-sm text-destructive">
              {formError}
            </p>
          )}
        </form>
        <DialogFooter>
          <Button variant="outline" onClick={close} disabled={saving}>
            Cancelar
          </Button>
          <Button type="submit" form="create-user-form" disabled={saving}>
            {saving && (
              <Loader2Icon className="animate-spin" data-icon="inline-start" />
            )}
            Crear usuario
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function TextField({
  name,
  label,
  error,
  ...props
}: {
  name: Field
  label: string
  error?: string
} & Omit<React.ComponentProps<typeof Input>, "name">) {
  const id = `new-user-${name}`
  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        name={name}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? `${id}-error` : undefined}
        className="h-9"
        {...props}
      />
      {error && (
        <p id={`${id}-error`} className="text-sm text-destructive">
          {error}
        </p>
      )}
    </div>
  )
}

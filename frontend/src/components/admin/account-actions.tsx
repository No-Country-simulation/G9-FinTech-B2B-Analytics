"use client"

import * as React from "react"
import { Loader2Icon } from "lucide-react"
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
import { ApiError, type AdminUser } from "@/lib/api"
import { useAuth } from "@/lib/auth"

export type AccountAction = "block" | "unblock" | "deactivate"

const COPY: Record<
  AccountAction,
  {
    label: string
    title: (name: string) => string
    description: (user: AdminUser) => string
    done: (name: string) => string
    destructive: boolean
  }
> = {
  block: {
    label: "Bloquear",
    title: (name) => `¿Bloquear a ${name}?`,
    description: () =>
      "Se cierran sus sesiones y no va a poder ingresar hasta que lo desbloquees. Sus tiendas se mantienen.",
    done: (name) => `Bloqueaste a ${name}.`,
    destructive: true,
  },
  unblock: {
    label: "Desbloquear",
    title: (name) => `¿Desbloquear a ${name}?`,
    description: () =>
      "Va a poder ingresar de nuevo. Si nunca definió su contraseña, vuelve a pendiente y vas a tener que reenviarle el correo de acceso.",
    done: (name) => `Desbloqueaste a ${name}.`,
    destructive: false,
  },
  deactivate: {
    label: "Dar de baja",
    title: (name) => `¿Dar de baja a ${name}?`,
    description: () =>
      "Es definitivo: se cierran sus sesiones y la cuenta no puede volver a ingresar.",
    done: (name) => `Diste de baja a ${name}.`,
    destructive: true,
  },
}

export function accountActionLabel(action: AccountAction) {
  return COPY[action].label
}

// What an admin can do with an account. Nothing on their own account, and
// deactivation is final.
export function availableAccountActions(
  user: AdminUser,
  currentUserId: string | undefined
): AccountAction[] {
  if (user.id === currentUserId) return []
  switch (user.status) {
    case "active":
    case "pending":
      return ["block", "deactivate"]
    case "blocked":
      return ["unblock", "deactivate"]
    case "deactivated":
      return []
  }
}

export function AccountActionDialog({
  user,
  action,
  onClose,
  onDone,
}: {
  user: AdminUser
  action: AccountAction | null
  onClose: () => void
  onDone: (user: AdminUser) => void
}) {
  const { request } = useAuth()
  const [pending, setPending] = React.useState(false)
  // Keeps the copy while the dialog animates out after `action` is cleared.
  const [shown, setShown] = React.useState<AccountAction>(action ?? "block")
  if (action && action !== shown) setShown(action)
  const copy = COPY[shown]

  async function confirm() {
    setPending(true)
    try {
      const updated = await request<AdminUser>(
        `/admin/users/${user.id}/${shown}`,
        { method: "POST" }
      )
      toast.success(copy.done(user.name))
      onDone(updated)
      onClose()
    } catch (err) {
      toast.error(
        err instanceof ApiError ? err.message : "No pudimos completar la acción."
      )
    } finally {
      setPending(false)
    }
  }

  return (
    <Dialog
      open={action !== null}
      onOpenChange={(open) => !open && !pending && onClose()}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{copy.title(user.name)}</DialogTitle>
          <DialogDescription>{copy.description(user)}</DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={pending}>
            Cancelar
          </Button>
          <Button
            className={
              copy.destructive
                ? "bg-destructive text-white hover:bg-destructive/90"
                : undefined
            }
            onClick={confirm}
            disabled={pending}
          >
            {pending && (
              <Loader2Icon className="animate-spin" data-icon="inline-start" />
            )}
            {copy.label}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

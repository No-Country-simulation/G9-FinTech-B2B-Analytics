import { ShieldCheckIcon, UserIcon } from "lucide-react"

import type { Tone } from "@/components/admin/tone"
import type { Role, StoreCategory, UserStatus } from "@/lib/api"

export const ROLE_LABELS: Record<Role, string> = {
  client: "Cliente",
  admin: "Admin",
}

export const STATUS_LABELS: Record<UserStatus, string> = {
  active: "Activo",
  pending: "Pendiente",
  blocked: "Bloqueado",
  deactivated: "Baja",
}

export const STATUS_TONES: Record<UserStatus, Tone> = {
  active: "emerald",
  pending: "amber",
  blocked: "red",
  deactivated: "neutral",
}

export const STORE_CATEGORY_LABELS: Record<StoreCategory, string> = {
  supermarket: "Supermercado",
  electronics: "Electrónica",
  fashion: "Moda",
}

export function RoleLabel({ role }: { role: Role }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      {role === "admin" ? (
        <ShieldCheckIcon className="size-4 text-violet-600 dark:text-violet-400" />
      ) : (
        <UserIcon className="size-4 text-sky-600 dark:text-sky-400" />
      )}
      {ROLE_LABELS[role]}
    </span>
  )
}

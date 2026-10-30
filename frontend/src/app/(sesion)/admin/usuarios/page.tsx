import type { Metadata } from "next"

import { UsersPanel } from "@/components/admin/users-panel"

export const metadata: Metadata = {
  title: "Usuarios · PriceScope",
}

export default function UsuariosPage() {
  return <UsersPanel />
}

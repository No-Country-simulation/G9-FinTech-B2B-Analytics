import type { Metadata } from "next"

import { DemoRequestsPanel } from "@/components/admin/demo-requests-panel"

export const metadata: Metadata = {
  title: "Solicitudes de demo · PriceScope",
}

export default function SolicitudesPage() {
  return <DemoRequestsPanel />
}

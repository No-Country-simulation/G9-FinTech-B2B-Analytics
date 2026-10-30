import { AdminShell } from "@/components/admin/admin-shell"

export default function AdminLayout({ children }: LayoutProps<"/admin">) {
  return <AdminShell>{children}</AdminShell>
}

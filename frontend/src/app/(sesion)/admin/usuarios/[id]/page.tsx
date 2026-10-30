import type { Metadata } from "next"
import { Suspense } from "react"

import { UserDetail, UserDetailSkeleton } from "@/components/admin/user-detail"

export const metadata: Metadata = {
  title: "Usuario · PriceScope",
}

// The id is only known at request time, so reading it sits behind Suspense.
export default function UsuarioPage({
  params,
}: PageProps<"/admin/usuarios/[id]">) {
  return (
    <Suspense fallback={<UserDetailSkeleton />}>
      <UserDetail params={params} />
    </Suspense>
  )
}

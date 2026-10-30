import type { Metadata } from "next"
import { Suspense } from "react"

import { CenteredShell } from "@/components/auth/centered-shell"
import { SetPasswordForm } from "@/components/auth/set-password-form"

export const metadata: Metadata = {
  title: "Restablecer contraseña · PriceScope",
}

// Landing page of the reset link sent by email (/restablecer/{token}).
export default function RestablecerPage() {
  return (
    <CenteredShell>
      <Suspense>
        <SetPasswordForm mode="reset" />
      </Suspense>
    </CenteredShell>
  )
}

import Link from "next/link"
import { ChartNoAxesCombinedIcon } from "lucide-react"

// Two-column frame shared by the access screens (login, password recovery).
export function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid min-h-svh lg:grid-cols-2">
      <div className="flex flex-col gap-4 px-6 py-8 md:px-10">
        <div className="flex flex-1 items-center justify-center py-10">
          <div className="flex w-full max-w-90 flex-col gap-8">
            <Link
              href="/"
              className="flex items-center gap-2 self-start font-semibold"
            >
              <span className="flex size-7 items-center justify-center rounded-md bg-brand text-white">
                <ChartNoAxesCombinedIcon className="size-4" />
              </span>
              PriceScope
            </Link>
            {children}
          </div>
        </div>
        <p className="mx-auto w-full max-w-90 text-xs text-muted-foreground">
          Las cuentas las crea el equipo de PriceScope después de la demo.
        </p>
      </div>
      {/* Reserved for the product visual; left blank for now. */}
      <div className="hidden bg-muted lg:block" />
    </div>
  )
}

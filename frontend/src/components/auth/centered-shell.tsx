import Link from "next/link"
import { ChartNoAxesCombinedIcon } from "lucide-react"

// Single centered card for the screens reached from an email link, so they
// read as a separate step from the login.
export function CenteredShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-6 bg-muted p-6 md:p-10">
      <div className="flex w-full max-w-sm flex-col gap-6">
        <Link
          href="/"
          className="flex items-center gap-2 self-center font-semibold"
        >
          <span className="flex size-7 items-center justify-center rounded-md bg-brand text-white">
            <ChartNoAxesCombinedIcon className="size-4" />
          </span>
          PriceScope
        </Link>
        {children}
      </div>
    </div>
  )
}

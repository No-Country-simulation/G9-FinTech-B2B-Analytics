import { AuthProvider } from "@/lib/auth"

// Routes that need the user's session: the login page and the backoffice.
export default function SessionLayout({ children }: LayoutProps<"/">) {
  return <AuthProvider>{children}</AuthProvider>
}

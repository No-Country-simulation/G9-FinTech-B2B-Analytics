import * as React from "react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"

// Soft color accents for the backoffice: a tinted background with readable
// text, used for badges, icon tiles and avatars. Surfaces stay neutral.
export const TONES = {
  brand: "bg-brand/10 text-brand-deep dark:bg-brand/20 dark:text-indigo-300",
  emerald:
    "bg-emerald-500/10 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400",
  amber:
    "bg-amber-500/10 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400",
  red: "bg-red-500/10 text-red-700 dark:bg-red-500/15 dark:text-red-400",
  sky: "bg-sky-500/10 text-sky-700 dark:bg-sky-500/15 dark:text-sky-400",
  violet:
    "bg-violet-500/10 text-violet-700 dark:bg-violet-500/15 dark:text-violet-400",
  neutral: "bg-muted text-muted-foreground",
} as const

export type Tone = keyof typeof TONES

export function ToneBadge({
  tone,
  className,
  children,
}: {
  tone: Tone
  className?: string
  children: React.ReactNode
}) {
  return (
    <span
      className={cn(
        "inline-flex h-5 w-fit shrink-0 items-center gap-1 rounded-md px-2 text-xs font-medium whitespace-nowrap [&>svg]:size-3",
        TONES[tone],
        className
      )}
    >
      {children}
    </span>
  )
}

export function IconTile({
  tone,
  children,
}: {
  tone: Tone
  children: React.ReactNode
}) {
  return (
    <span
      className={cn(
        "flex size-10 items-center justify-center rounded-lg [&>svg]:size-5",
        TONES[tone]
      )}
    >
      {children}
    </span>
  )
}

const AVATAR_TONES: Tone[] = ["brand", "emerald", "amber", "sky", "violet", "red"]

// Same name, same color, so a person is recognizable across visits.
function toneFor(name: string): Tone {
  let hash = 0
  for (const char of name) hash = (hash * 31 + char.charCodeAt(0)) >>> 0
  return AVATAR_TONES[hash % AVATAR_TONES.length]
}

function initials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("")
}

export function InitialsAvatar({
  name,
  size = "default",
  className,
}: {
  name: string
  size?: "default" | "lg"
  className?: string
}) {
  return (
    <Avatar className={cn(size === "lg" ? "size-20" : "size-9", className)}>
      <AvatarFallback
        className={cn(
          "font-semibold",
          size === "lg" ? "text-xl" : "text-xs",
          TONES[toneFor(name)]
        )}
      >
        {initials(name)}
      </AvatarFallback>
    </Avatar>
  )
}

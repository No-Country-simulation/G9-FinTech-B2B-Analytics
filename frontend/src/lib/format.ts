// Dates are shown in Argentina time, whatever the admin's browser zone is,
// because demo calls are scheduled in that zone.
const TIME_ZONE = "America/Argentina/Buenos_Aires"

const dateTime = new Intl.DateTimeFormat("es-AR", {
  timeZone: TIME_ZONE,
  weekday: "short",
  day: "numeric",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
})

const date = new Intl.DateTimeFormat("es-AR", {
  timeZone: TIME_ZONE,
  day: "numeric",
  month: "short",
  year: "numeric",
})

const shortDate = new Intl.DateTimeFormat("es-AR", {
  timeZone: TIME_ZONE,
  day: "numeric",
  month: "short",
})

export function formatShortDate(iso: string) {
  return shortDate.format(new Date(iso))
}

export function formatDateTime(iso: string) {
  return dateTime.format(new Date(iso))
}

export function formatDate(iso: string) {
  return date.format(new Date(iso))
}

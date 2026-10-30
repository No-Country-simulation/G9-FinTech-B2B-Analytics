"use client";

import * as React from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeftIcon,
  CheckIcon,
  CircleAlertIcon,
  CircleCheckIcon,
  CircleIcon,
  EyeIcon,
  EyeOffIcon,
  Loader2Icon,
  TriangleAlertIcon,
} from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button, buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ApiError, apiFetch } from "@/lib/api";
import { HOME_BY_ROLE, useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";

type TokenStatus = "checking" | "valid" | "expired" | "invalid";

type TokenInfo = {
  status: "valid" | "expired" | "invalid";
  email: string | null;
  company: string | null;
};

// "define": first password, from the welcome email the admin triggers.
// "reset": new password, from the link the user asked for in /recuperar.
type Mode = "define" | "reset";

const COPY = {
  define: {
    title: "Te damos la bienvenida a PriceScope",
    cta: "Definir contraseña e ingresar",
    pending: "Ingresando…",
    expired:
      "Los enlaces de bienvenida duran 72 horas. Pedile uno nuevo al equipo de PriceScope.",
    invalid:
      "Revisá que hayas copiado el enlace completo del correo, o pedile uno nuevo al equipo de PriceScope.",
  },
  reset: {
    title: "Restablecé tu contraseña",
    cta: "Guardar contraseña nueva",
    pending: "Guardando…",
    expired: "Los enlaces para restablecer duran 1 hora. Pedí uno nuevo.",
    invalid: "Revisá que hayas copiado el enlace completo, o pedí uno nuevo.",
  },
} satisfies Record<Mode, Record<string, string>>;

// Same rules the API enforces in validate_password.
function passwordRules(password: string, confirmation: string) {
  return [
    { label: "Mínimo 8 caracteres", ok: password.length >= 8 },
    { label: "Una mayúscula", ok: /[A-ZÁÉÍÓÚÑ]/.test(password) },
    { label: "Un número", ok: /[0-9]/.test(password) },
    {
      label: "Las contraseñas coinciden",
      ok: password.length > 0 && password === confirmation,
    },
  ];
}

export function SetPasswordForm({ mode }: { mode: Mode }) {
  const { token } = useParams<{ token: string }>();
  const router = useRouter();
  const { login } = useAuth();
  const copy = COPY[mode];

  const [status, setStatus] = React.useState<TokenStatus>("checking");
  const [owner, setOwner] = React.useState<TokenInfo | null>(null);
  const [password, setPassword] = React.useState("");
  const [confirmation, setConfirmation] = React.useState("");
  const [pending, setPending] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [done, setDone] = React.useState(false);

  // Check the link before asking for a password, so an expired one says so
  // up front instead of after the user typed it twice.
  React.useEffect(() => {
    let cancelled = false;
    apiFetch<TokenInfo>("/auth/token/verify", {
      method: "POST",
      body: JSON.stringify({ token }),
    })
      .then((data) => {
        if (cancelled) return;
        setOwner(data);
        setStatus(data.status);
      })
      .catch(() => !cancelled && setStatus("invalid"));
    return () => {
      cancelled = true;
    };
  }, [token]);

  const rules = passwordRules(password, confirmation);
  const allOk = rules.every((rule) => rule.ok);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!allOk) return;
    setPending(true);
    setError(null);
    try {
      await apiFetch("/auth/password", {
        method: "POST",
        body: JSON.stringify({ token, password }),
      });
    } catch (err) {
      if (err instanceof ApiError && err.status < 500) {
        setError(err.message);
      } else {
        setError("No pudimos conectar con el servidor. Probá de nuevo.");
      }
      setPending(false);
      return;
    }
    if (mode === "define" && owner?.email) {
      // First access: sign in right away instead of sending them to log in.
      // The link is already spent, so if this fails they log in by hand.
      try {
        const user = await login(owner.email, password);
        router.replace(HOME_BY_ROLE[user.role]);
        return;
      } catch {
        // Falls through to the success card.
      }
    }
    setDone(true);
    setPending(false);
  }

  if (status === "checking") {
    return (
      <Card>
        <CardContent className="flex items-center justify-center gap-2 py-10 text-sm text-muted-foreground">
          <Loader2Icon className="size-4 animate-spin" />
          Verificando el enlace…
        </CardContent>
      </Card>
    );
  }

  if (status !== "valid") {
    return (
      <Card>
        <CardHeader className="items-center text-center">
          <span className="mx-auto mb-2 flex size-11 items-center justify-center rounded-full bg-destructive/10 text-destructive">
            <TriangleAlertIcon className="size-5" />
          </span>
          <CardTitle className="text-xl">
            {status === "expired"
              ? "El enlace venció"
              : "El enlace no es válido"}
          </CardTitle>
          <CardDescription>
            {status === "expired" ? copy.expired : copy.invalid}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {/* Only the admin can resend a welcome link; resets are self-service. */}
          {mode === "reset" ? (
            <>
              <Link
                href="/recuperar"
                className={buttonVariants({ size: "lg", className: "h-10" })}
              >
                Pedir un enlace nuevo
              </Link>
              <BackToLogin />
            </>
          ) : (
            <Link
              href="/ingresar"
              className={buttonVariants({
                variant: "outline",
                size: "lg",
                className: "h-10",
              })}
            >
              Volver a ingresar
            </Link>
          )}
        </CardContent>
      </Card>
    );
  }

  if (done) {
    return (
      <Card role="status">
        <CardHeader className="items-center text-center">
          <span className="mx-auto mb-2 flex size-11 items-center justify-center rounded-full bg-muted">
            <CircleCheckIcon className="size-5" />
          </span>
          <CardTitle className="text-xl">
            {mode === "define"
              ? "Contraseña guardada"
              : "Contraseña actualizada"}
          </CardTitle>
          <CardDescription>
            {mode === "define"
              ? "Tu cuenta ya está activa. Ingresá con tu correo y la contraseña que elegiste."
              : "Tu contraseña quedó guardada. Ya podés ingresar con la nueva."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Link
            href="/ingresar"
            className={buttonVariants({ size: "lg", className: "h-10 w-full" })}
          >
            Ir a ingresar
          </Link>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">{copy.title}</CardTitle>
        <CardDescription>
          {mode === "define" ? (
            <>
              {owner?.company ? (
                <strong className="text-foreground">{owner.company}</strong>
              ) : (
                "Tu empresa"
              )}{" "}
              ya tiene su cuenta. Definí tu contraseña para ingresar.
            </>
          ) : (
            <>
              Elegí una contraseña nueva para{" "}
              {owner?.email ? (
                <strong className="text-foreground">{owner.email}</strong>
              ) : (
                "tu cuenta"
              )}
              .
            </>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          {error ? (
            <Alert variant="destructive">
              <CircleAlertIcon />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}

          <PasswordField
            id="password"
            label="Nueva contraseña"
            value={password}
            onChange={setPassword}
          />
          <PasswordField
            id="confirmation"
            label="Confirmar contraseña"
            value={confirmation}
            onChange={setConfirmation}
          />

          <ul id="password-rules" className="flex flex-col gap-1.5 text-sm">
            {rules.map((rule) => (
              <li
                key={rule.label}
                className={cn(
                  "flex items-center gap-2",
                  rule.ok ? "text-emerald-700" : "text-muted-foreground",
                )}
              >
                {rule.ok ? (
                  <CheckIcon className="size-4" />
                ) : (
                  <CircleIcon className="size-4" />
                )}
                {rule.label}
              </li>
            ))}
          </ul>

          <Button
            type="submit"
            size="lg"
            className="h-10"
            disabled={pending || !allOk}
          >
            {pending && <Loader2Icon className="animate-spin" />}
            {pending ? copy.pending : copy.cta}
          </Button>

          {mode === "reset" && <BackToLogin />}
        </form>
      </CardContent>
    </Card>
  );
}

function PasswordField({
  id,
  label,
  value,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  const [shown, setShown] = React.useState(false);
  return (
    <div className="flex flex-col gap-2">
      <Label htmlFor={id}>{label}</Label>
      <div className="relative">
        <Input
          id={id}
          type={shown ? "text" : "password"}
          autoComplete="new-password"
          required
          value={value}
          onChange={(event) => onChange(event.target.value)}
          aria-describedby="password-rules"
          className="h-10 pr-10"
        />
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          className="absolute top-1/2 right-1.5 -translate-y-1/2 text-muted-foreground"
          onClick={() => setShown((value) => !value)}
          aria-label={shown ? "Ocultar contraseña" : "Mostrar contraseña"}
          aria-pressed={shown}
        >
          {shown ? <EyeOffIcon /> : <EyeIcon />}
        </Button>
      </div>
    </div>
  );
}

function BackToLogin() {
  return (
    <Link
      href="/ingresar"
      className="flex items-center justify-center gap-1.5 text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
    >
      <ArrowLeftIcon className="size-4" />
      Volver a ingresar
    </Link>
  );
}

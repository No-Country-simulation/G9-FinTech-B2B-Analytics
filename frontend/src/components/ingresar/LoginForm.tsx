"use client";

import { useState } from "react";
import Link from "next/link";

export function LoginForm() {
  const [pwShown, setPwShown] = useState(false);
  const [error, setError] = useState(false);

  return (
    <div className="mx-auto flex w-full max-w-[420px] flex-col gap-8">
      <div className="flex flex-col gap-2.5">
        <h1 className="m-0 font-serif text-[46px] font-light leading-[1.05] tracking-[-0.03em]">
          Ingresar
        </h1>
        <p className="m-0 text-[15.5px] text-ink-soft">
          ¿No tenés cuenta?{" "}
          <Link
            href="/registro"
            className="font-medium text-brand-deep underline"
          >
            Crear cuenta
          </Link>
        </p>
      </div>

      <form
        className="flex flex-col gap-5"
        onSubmit={(e) => {
          e.preventDefault();
          setError(true);
        }}
      >
        {error && (
          <div
            role="alert"
            className="flex items-start gap-2.5 rounded-[10px] bg-danger-bg px-3.5 py-3 text-sm font-medium text-danger-ink"
          >
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              aria-hidden="true"
              className="mt-px flex-none"
            >
              <circle cx="12" cy="12" r="9" />
              <path d="M12 7v6M12 16.5v.5" />
            </svg>
            Correo o contraseña incorrectos.
          </div>
        )}

        <div className="flex flex-col gap-2">
          <label
            htmlFor="email"
            className="text-[13.5px] font-medium text-[#3E4057]"
          >
            Correo electrónico
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="nombre@empresa.com"
            className="min-h-[52px] rounded-[10px] border border-line bg-white px-4 text-base text-ink"
          />
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex items-baseline justify-between gap-3">
            <label
              htmlFor="pw"
              className="text-[13.5px] font-medium text-[#3E4057]"
            >
              Contraseña
            </label>
            <a
              href="#recuperar"
              className="text-[13.5px] text-brand-deep underline"
            >
              ¿Olvidaste tu contraseña?
            </a>
          </div>
          <div className="flex gap-2">
            <input
              id="pw"
              type={pwShown ? "text" : "password"}
              autoComplete="current-password"
              className="min-h-[52px] min-w-0 flex-1 rounded-[10px] border border-line bg-white px-4 text-base text-ink"
            />
            <button
              type="button"
              onClick={() => setPwShown(!pwShown)}
              aria-pressed={pwShown}
              className="min-h-[52px] cursor-pointer rounded-[10px] border border-line bg-white px-4 text-sm font-medium text-ink"
            >
              {pwShown ? "Ocultar" : "Mostrar"}
            </button>
          </div>
        </div>

        <button
          type="submit"
          className="min-h-[54px] cursor-pointer rounded-xl bg-brand text-base font-medium text-white shadow-[0_12px_24px_-14px_rgba(74,91,219,.9)]"
        >
          Ingresar
        </button>
      </form>
    </div>
  );
}

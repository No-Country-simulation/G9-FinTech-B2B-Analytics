"use client";

import { useState } from "react";
import Link from "next/link";

const checks = (pw: string) => [
  { ok: pw.length >= 8, text: "Mínimo 8 caracteres" },
  { ok: /[A-ZÁÉÍÓÚÑ]/.test(pw), text: "Una mayúscula" },
  { ok: /[0-9]/.test(pw), text: "Un número" },
];

const inputCls =
  "min-h-[52px] rounded-[10px] border border-line bg-white px-4 text-base text-ink";

const labelCls = "text-[13.5px] font-medium text-[#3E4057]";

export function RegistroForm() {
  const [pw, setPw] = useState("");

  const results = checks(pw);
  const n = results.filter((c) => c.ok).length;
  const on = n === 3 ? "#1B7A55" : n === 2 ? "#B7791F" : "#B4325A";
  const off = "#DDDFEA";

  return (
    <div className="mx-auto flex w-full max-w-[460px] flex-col gap-8">
      <div className="flex flex-col gap-2.5">
        <h1 className="m-0 font-serif text-[46px] font-light leading-[1.05] tracking-[-0.03em]">
          Crear cuenta
        </h1>
        <p className="m-0 text-[15.5px] text-ink-soft">
          ¿Ya tenés cuenta?{" "}
          <Link href="/ingresar" className="font-medium text-brand-deep underline">
            Ingresar
          </Link>
        </p>
      </div>

      <form
        className="flex flex-col gap-[18px]"
        onSubmit={(e) => e.preventDefault()}
      >
        <div className="grid grid-cols-[repeat(auto-fit,minmax(min(200px,100%),1fr))] gap-4">
          <div className="flex flex-col gap-2">
            <label htmlFor="nombre" className={labelCls}>
              Nombre y apellido
            </label>
            <input
              id="nombre"
              type="text"
              autoComplete="name"
              className={inputCls}
            />
          </div>
          <div className="flex flex-col gap-2">
            <label htmlFor="empresa" className={labelCls}>
              Empresa
            </label>
            <input
              id="empresa"
              type="text"
              autoComplete="organization"
              className={inputCls}
            />
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="correo" className={labelCls}>
            Correo laboral
          </label>
          <input
            id="correo"
            type="email"
            autoComplete="email"
            placeholder="nombre@empresa.com"
            className={inputCls}
          />
        </div>

        <div className="flex flex-col gap-2.5">
          <label htmlFor="pw" className={labelCls}>
            Contraseña
          </label>
          <input
            id="pw"
            type="password"
            autoComplete="new-password"
            value={pw}
            onChange={(e) => setPw(e.target.value)}
            aria-describedby="reglas"
            className={inputCls}
          />
          <div className="flex items-center gap-3">
            <div
              className="grid flex-1 grid-cols-3 gap-1"
              aria-hidden="true"
            >
              <span
                className="h-1 rounded-sm"
                style={{ background: n >= 1 ? on : off }}
              />
              <span
                className="h-1 rounded-sm"
                style={{ background: n >= 2 ? on : off }}
              />
              <span
                className="h-1 rounded-sm"
                style={{ background: n >= 3 ? on : off }}
              />
            </div>
            <span className="min-w-[52px] text-[13px] font-medium text-[#4B4D63]">
              {n === 3 ? "Fuerte" : n === 2 ? "Media" : "Débil"}
            </span>
          </div>
          <ul
            id="reglas"
            className="m-0 flex list-none flex-col gap-1 p-0 text-[13.5px]"
          >
            {results.map((r) => (
              <li
                key={r.text}
                className="flex items-center gap-2"
                style={{ color: r.ok ? "#14664A" : "#5C5E73" }}
              >
                <span
                  aria-hidden="true"
                  className="w-4 text-center font-semibold"
                >
                  {r.ok ? "✓" : "○"}
                </span>
                {r.text}
                <span className="sr-only">
                  {r.ok ? " (cumplida)" : " (pendiente)"}
                </span>
              </li>
            ))}
          </ul>
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="pw2" className={labelCls}>
            Repetí la contraseña
          </label>
          <input
            id="pw2"
            type="password"
            autoComplete="new-password"
            className={inputCls}
          />
        </div>

        <div className="flex items-start gap-3">
          <input
            id="terminos"
            type="checkbox"
            className="mt-px h-5 w-5 flex-none accent-brand"
          />
          <label
            htmlFor="terminos"
            className="text-[13.5px] leading-relaxed text-[#4B4D63]"
          >
            Acepto los{" "}
            <a href="#terminos" className="text-brand-deep underline">
              términos y condiciones
            </a>{" "}
            y la{" "}
            <a href="#privacidad" className="text-brand-deep underline">
              política de privacidad
            </a>
            .
          </label>
        </div>

        <button
          type="submit"
          className="min-h-[54px] cursor-pointer rounded-xl bg-brand text-[16.5px] font-medium text-white shadow-[0_12px_24px_-14px_rgba(74,91,219,.9)]"
        >
          Crear cuenta
        </button>
      </form>
    </div>
  );
}

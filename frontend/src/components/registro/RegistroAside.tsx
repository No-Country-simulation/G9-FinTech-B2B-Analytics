import Link from "next/link";

const steps = [
  { n: "1", text: "Completás tus datos", current: true },
  { n: "2", text: "Confirmás tu correo", current: false },
  { n: "3", text: "Entrás a tu tablero", current: false },
];

export function RegistroAside() {
  return (
    <aside className="flex min-h-[420px] flex-1 basis-[480px] flex-col justify-between gap-10 bg-lilac px-14 py-11 text-ink [background-image:radial-gradient(ellipse_80%_60%_at_10%_100%,rgba(98,112,255,.22),transparent_70%)]">
      <Link
        href="/"
        className="flex items-center gap-3 text-[15px] font-semibold tracking-[.22em]"
      >
        <svg width="26" height="26" viewBox="0 0 28 28" aria-hidden="true">
          <rect width="28" height="28" rx="7" fill="#1C1D2B" />
          <path
            d="M6 20 L11 13 L15 16 L22 7"
            fill="none"
            stroke="#fff"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        PRICESCOPE
      </Link>

      <div className="flex flex-col gap-10">
        <h2 className="m-0 font-serif text-[clamp(42px,5vw,72px)] font-light leading-[1.02] tracking-[-0.03em] text-balance">
          Creá tu cuenta y mirá lo que el dólar{" "}
          <em className="text-brand-deep">esconde</em>.
        </h2>
        <ol className="m-0 flex max-w-[420px] list-none flex-col p-0">
          {steps.map((s) => (
            <li
              key={s.n}
              className={`flex items-center gap-4 border-t border-line-soft px-0 py-4 font-medium ${
                s.current ? "" : "text-[#3E4057]"
              } ${s.n === "3" ? "border-b" : ""}`}
            >
              <span
                className={`inline-flex h-[30px] w-[30px] flex-none items-center justify-center rounded-full text-[13px] ${
                  s.current
                    ? "bg-brand text-white"
                    : "border border-[#8A90C8] text-inherit"
                }`}
              >
                {s.n}
              </span>
              {s.text}
            </li>
          ))}
        </ol>
      </div>
    </aside>
  );
}

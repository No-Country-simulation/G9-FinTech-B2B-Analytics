import Link from "next/link";

export function IngresarAside() {
  return (
    <aside className="relative flex min-h-[420px] flex-1 basis-[520px] flex-col justify-between gap-10 overflow-hidden bg-navy px-14 py-11 text-white [background-image:radial-gradient(ellipse_80%_60%_at_90%_0%,rgba(98,112,255,.35),transparent_70%)]">
      <Link
        href="/"
        className="flex items-center gap-3 text-[15px] font-semibold tracking-[.22em]"
      >
        <svg width="26" height="26" viewBox="0 0 28 28" aria-hidden="true">
          <rect width="28" height="28" rx="7" fill="#fff" />
          <path
            d="M6 20 L11 13 L15 16 L22 7"
            fill="none"
            stroke="#14163A"
            strokeWidth="2.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        PRICESCOPE
      </Link>

      <div className="flex flex-col gap-9">
        <h2 className="m-0 font-serif text-[clamp(42px,5vw,72px)] font-light leading-[1.02] tracking-[-0.03em] text-balance">
          Volvé a ver la inflación{" "}
          <em className="text-periwinkle">real</em>.
        </h2>

        <svg
          viewBox="0 0 520 170"
          width="100%"
          aria-hidden="true"
          className="block max-w-[560px] overflow-visible"
        >
          <defs>
            <linearGradient id="ga" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#8A98FF" stopOpacity=".35" />
              <stop offset="1" stopColor="#8A98FF" stopOpacity="0" />
            </linearGradient>
          </defs>
          <polygon
            fill="url(#ga)"
            points="0,130 60,124 120,126 180,106 240,96 300,80 360,66 420,48 480,32 480,170 0,170"
          />
          <polyline
            fill="none"
            stroke="#6A6F9E"
            strokeWidth="2"
            strokeDasharray="6 5"
            points="0,130 60,128 120,122 180,112 240,104 300,92 360,78 420,64 480,52"
          />
          <polyline
            fill="none"
            stroke="#AEB8FF"
            strokeWidth="3"
            strokeLinejoin="round"
            strokeLinecap="round"
            points="0,130 60,124 120,126 180,106 240,96 300,80 360,66 420,48 480,32"
          />
          <circle cx="480" cy="32" r="5" fill="#fff" />
        </svg>

        <div className="flex flex-wrap gap-10 border-t border-line-dark pt-5">
          <div>
            <div className="text-[11.5px] tracking-[.16em] text-periwinkle-soft">
              EN PESOS
            </div>
            <div className="mt-1 text-[32px] font-light tracking-[-0.03em]">
              +11,7 %
            </div>
          </div>
          <div>
            <div className="text-[11.5px] tracking-[.16em] text-periwinkle-soft">
              EN DÓLARES
            </div>
            <div className="mt-1 text-[32px] font-light tracking-[-0.03em]">
              +2,0 %
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}

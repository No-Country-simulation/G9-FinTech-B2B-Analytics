import type { Metadata } from "next";
import { DemoHeader } from "@/components/demo/DemoHeader";
import { DemoBooking } from "@/components/demo/DemoBooking";
import "./demo.css";

export const metadata: Metadata = {
  title: "Agendar demo · PriceScope",
};

export default function DemoPage() {
  return (
    <div className="min-h-[900px] bg-[#F4F5F8] text-[#171A21]">
      <DemoHeader />
      <main className="mx-auto flex max-w-[1100px] flex-wrap items-start gap-10 px-8 pb-16 pt-6">
        <section className="flex min-w-[300px] flex-1 basis-[360px] flex-col gap-5 pt-3">
          <span className="eyebrow">Demo comercial</span>
          <h1 className="h2">Mirá PriceScope con tus categorías.</h1>
          <p className="lead">
            En 30 minutos recorremos el dashboard, la matriz de precios y las
            alertas con datos de tu sector.
          </p>
          <ul className="m-0 flex list-none flex-col gap-3 p-0">
            <li className="chk">
              <svg
                className="ic"
                viewBox="0 0 24 24"
                aria-hidden="true"
                style={{ color: "#157347" }}
              >
                <path d="M5 12l4 4 10-10" />
              </svg>
              <span>
                Inflación acumulada en pesos y en dólares, con la brecha contra
                el oficial y el blue.
              </span>
            </li>
            <li className="chk">
              <svg
                className="ic"
                viewBox="0 0 24 24"
                aria-hidden="true"
                style={{ color: "#157347" }}
              >
                <path d="M5 12l4 4 10-10" />
              </svg>
              <span>
                Cómo tratamos promociones y reduflación para que el índice no
                se distorsione.
              </span>
            </li>
            <li className="chk">
              <svg
                className="ic"
                viewBox="0 0 24 24"
                aria-hidden="true"
                style={{ color: "#157347" }}
              >
                <path d="M5 12l4 4 10-10" />
              </svg>
              <span>
                Alertas para productos que suben más que la devaluación y para
                hitos como CyberWeek.
              </span>
            </li>
          </ul>
        </section>

        <DemoBooking />
      </main>
    </div>
  );
}

import type { Metadata } from "next";
import { IngresarAside } from "@/components/ingresar/IngresarAside";
import { LoginForm } from "@/components/ingresar/LoginForm";

export const metadata: Metadata = {
  title: "Ingresar · PriceScope",
};

export default function IngresarPage() {
  return (
    <div className="flex min-h-[900px] flex-wrap bg-white text-ink">
      <IngresarAside />
      <main className="flex flex-1 basis-[480px] flex-col justify-center bg-white px-8 py-12">
        <LoginForm />
      </main>
    </div>
  );
}

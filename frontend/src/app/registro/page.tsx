import type { Metadata } from "next";
import { RegistroAside } from "@/components/registro/RegistroAside";
import { RegistroForm } from "@/components/registro/RegistroForm";

export const metadata: Metadata = {
  title: "Crear cuenta · PriceScope",
};

export default function RegistroPage() {
  return (
    <div className="flex min-h-[1040px] flex-wrap bg-white text-ink">
      <RegistroAside />
      <main className="flex flex-1 basis-[520px] flex-col justify-center px-8 py-12">
        <RegistroForm />
      </main>
    </div>
  );
}

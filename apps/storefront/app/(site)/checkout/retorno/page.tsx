import Link from "next/link";

export const dynamic = "force-dynamic";
export const metadata = {
  title: "Pago | Growup",
  robots: { index: false, follow: false },
};

export default async function CheckoutRetornoPage({
  searchParams,
}: {
  searchParams: Promise<{ id?: string; env?: string }>;
}) {
  const { id } = await searchParams;

  return (
    <main className="mx-auto flex min-h-[60vh] max-w-xl flex-col items-center justify-center gap-4 p-10 text-center">
      <p className="label text-[var(--muted)]">[ pago ]</p>
      <h1 className="display text-3xl">Gracias por tu compra</h1>
      <p className="text-[var(--muted)]">
        Estamos confirmando tu pago con la pasarela. Recibirás un correo con el
        detalle de tu orden. Si el cobro no se completa, tu orden quedará
        pendiente y podrás intentarlo de nuevo.
      </p>
      {id ? (
        <p className="label text-[var(--muted)]">referencia: {id}</p>
      ) : null}
      <Link href="/collection" className="label mt-2 underline underline-offset-4">
        Seguir explorando
      </Link>
    </main>
  );
}

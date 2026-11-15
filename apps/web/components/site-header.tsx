import Link from "next/link";

import { site } from "@/content/site";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-40 border-b border-black/10 bg-white/75 backdrop-blur-xl">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-6 px-6 py-4 md:px-10">
        <Link href="/" className="display text-xl leading-none text-[#0d0d0d]">
          growup<span aria-hidden className="text-[#0d0d0d]">.</span>
        </Link>
        <nav aria-label="Principal" className="hidden items-center gap-8 md:flex">
          <Link href="/servicios" className="label text-[#525866] transition-colors hover:text-[#0d0d0d]">
            Servicios
          </Link>
          <Link href="/planes" className="label text-[#525866] transition-colors hover:text-[#0d0d0d]">
            Planes
          </Link>
          <a
            href={site.admin_url}
            className="label text-[#525866] transition-colors hover:text-[#0d0d0d]"
            target="_blank"
            rel="noopener noreferrer"
          >
            Consola
          </a>
        </nav>
        <a
          href={site.admin_login_url}
          className="nova-cta label inline-flex min-h-[40px] items-center rounded-xl border border-[#0d0d0d] bg-[#0d0d0d] px-5 py-2.5 font-semibold text-white transition-transform hover:-translate-y-0.5"
        >
          Iniciar sesión
        </a>
      </div>
    </header>
  );
}

"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function NavLink({ href, label }: { href: string; label: string }) {
  const pathname = usePathname();
  const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
  return (
    <Link
      href={href}
      aria-current={active ? "page" : undefined}
      className={`flex items-center justify-between rounded-xl px-3.5 py-2.5 text-[13px] transition-all ${
        active
          ? "bg-[#0d0d0d] font-semibold text-white shadow-sm"
          : "text-[#525866] hover:bg-black/5 hover:text-[#0d0d0d]"
      }`}
    >
      <span>{label}</span>
      <span className={`h-1.5 w-1.5 rounded-full ${active ? "bg-white" : "bg-black/15"}`} />
    </Link>
  );
}

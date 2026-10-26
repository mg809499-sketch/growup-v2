"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export function NavLink({
  href,
  label,
}: {
  href: string;
  label: string;
}) {
  const pathname = usePathname();
  const active = href === "/" ? pathname === "/" : pathname.startsWith(href);

  return (
    <Link
      href={href}
      className={`flex items-center justify-between border-l-2 px-4 py-2.5 text-sm transition-colors ${
        active
          ? "border-white bg-white/10 text-white"
          : "border-transparent text-slate-400 hover:border-slate-600 hover:text-white"
      }`}
    >
      <span>{label}</span>
      <span className="mono text-[10px] text-slate-500">
        {active ? "•" : ""}
      </span>
    </Link>
  );
}

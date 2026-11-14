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
          ? "border-slate-900 bg-slate-100 text-slate-900"
          : "border-transparent text-slate-600 hover:border-slate-300 hover:text-slate-900"
      }`}
    >
      <span>{label}</span>
      <span className="mono text-[10px] text-slate-400">
        {active ? "•" : ""}
      </span>
    </Link>
  );
}

"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { logout } from "@/actions/auth";
import { cn } from "@/components/ui";

interface NavItem {
  href: string;
  label: string;
  adminOnly?: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/schichten", label: "Schichten" },
  { href: "/kunden", label: "Kunden", adminOnly: true },
  { href: "/mitarbeiter", label: "Mitarbeiter", adminOnly: true },
  { href: "/rechnungen", label: "Rechnungen", adminOnly: true },
  { href: "/auswertungen", label: "Auswertungen", adminOnly: true },
  { href: "/systemstatus", label: "Systemstatus", adminOnly: true },
  { href: "/protokoll", label: "Protokoll", adminOnly: true },
  { href: "/einstellungen", label: "Organisation", adminOnly: true },
];

export function Nav({
  isAdmin,
  fullName,
  role,
  organizationName,
}: {
  isAdmin: boolean;
  fullName: string;
  role: string;
  organizationName?: string;
}) {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const items = NAV_ITEMS.filter((item) => !item.adminOnly || isAdmin);
  const displayName = fullName || "Unbekannter Nutzer";
  const roleLabel = role === "admin" ? "Administrator" : "Mitarbeiter";
  const initials = displayName
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase() || "MP";

  const linkClass = (href: string) => {
    const active = pathname === href || pathname.startsWith(`${href}/`);
    return cn(
      "flex items-center justify-between rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
      active
        ? "bg-white text-slate-950 shadow-sm ring-1 ring-white/10"
        : "text-slate-300 hover:bg-slate-900 hover:text-white",
    );
  };

  const sidebar = (
    <aside
      className={cn(
        "fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-slate-900 bg-slate-950 px-4 py-5 text-white shadow-2xl transition-transform duration-200 md:translate-x-0",
        open ? "translate-x-0" : "-translate-x-full",
      )}
    >
      <div className="flex items-center justify-between gap-3 px-1">
        <Link href="/dashboard" className="min-w-0" onClick={() => setOpen(false)}>
          <div className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-300">
            Mouvin Personal
          </div>
          <div className="mt-1 truncate text-lg font-semibold tracking-tight text-white">
            {organizationName || "Organisation"}
          </div>
        </Link>
        <button
          type="button"
          className="rounded-lg p-2 text-slate-400 hover:bg-slate-900 hover:text-white md:hidden"
          onClick={() => setOpen(false)}
          aria-label="Menü schließen"
        >
          <span className="block h-5 w-5 text-center text-xl leading-4">×</span>
        </button>
      </div>

      <div className="mt-6 rounded-xl border border-slate-800 bg-slate-900/70 p-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-500 text-sm font-bold text-white">
            {initials}
          </div>
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold text-white">{displayName}</div>
            <div className="mt-0.5 text-xs text-slate-400">{roleLabel}</div>
          </div>
        </div>
        {isAdmin && (
          <div className="mt-3 rounded-lg bg-emerald-400/10 px-2.5 py-1.5 text-xs font-medium text-emerald-200 ring-1 ring-emerald-300/10">
            Admin-Zugriff aktiv
          </div>
        )}
      </div>

      <nav className="mt-6 space-y-1.5">
        {items.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={linkClass(item.href)}
            onClick={() => setOpen(false)}
          >
            <span>{item.label}</span>
            {(pathname === item.href || pathname.startsWith(`${item.href}/`)) && (
              <span className="h-1.5 w-1.5 rounded-full bg-indigo-500" />
            )}
          </Link>
        ))}
      </nav>

      <div className="mt-auto border-t border-slate-800 pt-4">
        <form action={logout}>
          <button className="flex w-full items-center justify-center rounded-lg border border-slate-800 px-3 py-2.5 text-sm font-medium text-slate-200 transition-colors hover:bg-slate-900 hover:text-white">
            Logout
          </button>
        </form>
      </div>
    </aside>
  );

  return (
    <>
      <div className="fixed inset-x-0 top-0 z-40 border-b border-slate-200 bg-white/95 px-4 py-3 shadow-sm backdrop-blur md:hidden">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">
              Mouvin Personal
            </div>
            <div className="truncate text-sm font-semibold text-slate-950">
              {organizationName || "Organisation"}
            </div>
          </div>
          <button
            type="button"
            className="rounded-lg border border-slate-200 p-2 text-slate-700 shadow-sm hover:bg-slate-50"
            onClick={() => setOpen(true)}
            aria-label="Menü öffnen"
          >
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M4 6h16M4 12h16M4 18h16" strokeLinecap="round" />
            </svg>
          </button>
        </div>
      </div>

      {open && (
        <button
          type="button"
          className="fixed inset-0 z-40 bg-slate-950/50 md:hidden"
          onClick={() => setOpen(false)}
          aria-label="Menü schließen"
        />
      )}
      {sidebar}
    </>
  );
}

"use client";

import { useFormStatus } from "react-dom";

import { cn } from "@/components/ui";

/** Submit-Button mit Sicherheitsabfrage (für destruktive Aktionen). */
export function ConfirmButton({
  children,
  message,
  variant = "danger",
}: {
  children: React.ReactNode;
  message: string;
  variant?: "danger" | "secondary";
}) {
  const { pending } = useFormStatus();
  const classes =
    variant === "danger"
      ? "border-red-300 text-red-700 hover:bg-red-50 dark:border-red-800 dark:text-red-300 dark:hover:bg-red-950"
      : "border-slate-300 text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800";
  return (
    <button
      type="submit"
      disabled={pending}
      onClick={(e) => {
        if (!window.confirm(message)) e.preventDefault();
      }}
      className={cn(
        "inline-flex items-center rounded-md border px-4 py-2 text-sm font-medium transition-colors disabled:opacity-60",
        classes,
      )}
    >
      {pending ? "Bitte warten …" : children}
    </button>
  );
}

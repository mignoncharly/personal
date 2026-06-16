import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from "react";

import Link from "next/link";

export function cn(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(" ");
}

type Variant = "primary" | "secondary" | "danger" | "ghost";
type Size = "sm" | "md";

const variantClasses: Record<Variant, string> = {
  primary:
    "bg-indigo-600 text-white shadow-sm shadow-indigo-600/20 hover:bg-indigo-500 disabled:bg-indigo-300",
  secondary:
    "border border-slate-200 bg-white text-slate-800 shadow-sm hover:bg-slate-50 disabled:opacity-60 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:hover:bg-slate-700",
  danger: "bg-red-600 text-white shadow-sm hover:bg-red-500 disabled:bg-red-300",
  ghost:
    "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800",
};

const sizeClasses: Record<Size, string> = {
  sm: "px-2.5 py-1.5 text-sm",
  md: "px-4 py-2 text-sm",
};

function buttonClass(variant: Variant, size: Size, extra?: string): string {
  return cn(
    "inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed",
    variantClasses[variant],
    sizeClasses[size],
    extra,
  );
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

export function Button({
  variant = "primary",
  size = "md",
  className,
  ...props
}: ButtonProps) {
  return <button className={buttonClass(variant, size, className)} {...props} />;
}

interface ButtonLinkProps {
  href: string;
  variant?: Variant;
  size?: Size;
  className?: string;
  children: ReactNode;
  /** Für Datei-Downloads: rendert ein echtes <a> (harte Navigation statt Client-Routing). */
  download?: boolean;
}

export function ButtonLink({
  href,
  variant = "primary",
  size = "md",
  className,
  children,
  download = false,
}: ButtonLinkProps) {
  const cls = buttonClass(variant, size, className);
  if (download) {
    return (
      <a href={href} className={cls}>
        {children}
      </a>
    );
  }
  return (
    <Link href={href} className={cls}>
      {children}
    </Link>
  );
}

export function Card({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-xl border border-slate-200 bg-white p-5 shadow-sm shadow-slate-200/70 dark:border-slate-700 dark:bg-slate-800 dark:shadow-none",
        className,
      )}
    >
      {children}
    </div>
  );
}


export function KpiCard({
  label,
  value,
  hint,
  accent = "indigo",
}: {
  label: string;
  value: ReactNode;
  hint?: ReactNode;
  accent?: "indigo" | "emerald" | "amber" | "rose" | "blue" | "slate";
}) {
  const accents: Record<string, string> = {
    indigo: "bg-indigo-500",
    emerald: "bg-emerald-500",
    amber: "bg-amber-500",
    rose: "bg-rose-500",
    blue: "bg-blue-500",
    slate: "bg-slate-500",
  };
  return (
    <Card className="relative overflow-hidden p-5">
      <div className={cn("absolute left-0 top-0 h-full w-1", accents[accent])} />
      <div className="text-sm font-medium text-slate-500 dark:text-slate-400">
        {label}
      </div>
      <div className="mt-2 text-2xl font-bold tracking-tight text-slate-950 dark:text-white">
        {value}
      </div>
      {hint && (
        <div className="mt-2 text-xs font-medium text-slate-500 dark:text-slate-400">
          {hint}
        </div>
      )}
    </Card>
  );
}
export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div className="min-w-0">
        <h1 className="text-3xl font-bold tracking-tight text-slate-950 dark:text-white">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500 dark:text-slate-400">
            {subtitle}
          </p>
        )}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

const labelClass =
  "block text-sm font-medium text-slate-700 dark:text-slate-200";
const controlClass =
  "mt-1 block w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500 disabled:bg-slate-100 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-100";

export function Field({
  label,
  htmlFor,
  hint,
  children,
}: {
  label: string;
  htmlFor?: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div>
      <label htmlFor={htmlFor} className={labelClass}>
        {label}
      </label>
      {children}
      {hint && (
        <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">{hint}</p>
      )}
    </div>
  );
}

export function Input(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={cn(controlClass, props.className)} />;
}

export function Textarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={cn(controlClass, props.className)} />;
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={cn(controlClass, props.className)} />;
}

export function Checkbox({
  label,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className="flex items-center gap-2 text-sm text-slate-700 dark:text-slate-200">
      <input
        type="checkbox"
        {...props}
        className="h-4 w-4 rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
      />
      {label}
    </label>
  );
}

type AlertKind = "error" | "success" | "info";

const alertClasses: Record<AlertKind, string> = {
  error:
    "border-red-200 bg-red-50 text-red-700 dark:border-red-900 dark:bg-red-950 dark:text-red-300",
  success:
    "border-green-200 bg-green-50 text-green-700 dark:border-green-900 dark:bg-green-950 dark:text-green-300",
  info: "border-slate-200 bg-slate-50 text-slate-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300",
};

export function Alert({
  kind = "info",
  children,
}: {
  kind?: AlertKind;
  children: ReactNode;
}) {
  if (!children) return null;
  return (
    <div className={cn("rounded-md border px-4 py-3 text-sm", alertClasses[kind])}>
      {children}
    </div>
  );
}

export function Badge({
  children,
  color = "slate",
}: {
  children: ReactNode;
  color?: "slate" | "amber" | "green" | "red" | "indigo" | "blue";
}) {
  const colors: Record<string, string> = {
    slate: "bg-slate-100 text-slate-700 ring-slate-200 dark:bg-slate-700 dark:text-slate-200 dark:ring-slate-600",
    amber: "bg-amber-50 text-amber-800 ring-amber-200 dark:bg-amber-900 dark:text-amber-200 dark:ring-amber-800",
    green: "bg-emerald-50 text-emerald-800 ring-emerald-200 dark:bg-green-900 dark:text-green-200 dark:ring-green-800",
    red: "bg-rose-50 text-rose-700 ring-rose-200 dark:bg-red-900 dark:text-red-200 dark:ring-red-800",
    indigo:
      "bg-indigo-50 text-indigo-700 ring-indigo-200 dark:bg-indigo-900 dark:text-indigo-200 dark:ring-indigo-800",
    blue: "bg-blue-50 text-blue-700 ring-blue-200 dark:bg-blue-900 dark:text-blue-200 dark:ring-blue-800",
  };
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset",
        colors[color],
      )}
    >
      {children}
    </span>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-300 bg-white p-10 text-center text-sm text-slate-500 shadow-sm dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-400">
      {children}
    </div>
  );
}

/** Seitennavigation für paginierte Listen. Rendert nichts bei nur einer Seite. */
export function Pagination({
  page,
  totalPages,
  count,
  makeHref,
}: {
  page: number;
  totalPages: number;
  count?: number;
  makeHref: (page: number) => string;
}) {
  if (totalPages <= 1) return null;
  const linkCls =
    "rounded-md border border-slate-300 px-3 py-1 font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800";
  return (
    <div className="mt-4 flex items-center justify-between text-sm">
      <span className="text-slate-500 dark:text-slate-400">
        Seite {page} von {totalPages}
        {count !== undefined ? ` · ${count} Einträge` : ""}
      </span>
      <div className="flex gap-2">
        {page > 1 && (
          <Link href={makeHref(page - 1)} className={linkCls}>
            Zurück
          </Link>
        )}
        {page < totalPages && (
          <Link href={makeHref(page + 1)} className={linkCls}>
            Weiter
          </Link>
        )}
      </div>
    </div>
  );
}

/** Tabellen-Primitive für konsistente Listen. */
export function Table({ children }: { children: ReactNode }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm shadow-slate-200/70 dark:border-slate-700 dark:bg-slate-800 dark:shadow-none">
      <table className="min-w-full divide-y divide-slate-200 text-sm dark:divide-slate-700">
        {children}
      </table>
    </div>
  );
}

export function Th({ children, className }: { children?: ReactNode; className?: string }) {
  return (
    <th
      className={cn(
        "bg-slate-50 px-4 py-3.5 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 dark:bg-slate-800 dark:text-slate-400",
        className,
      )}
    >
      {children}
    </th>
  );
}

export function Td({ children, className }: { children?: ReactNode; className?: string }) {
  return (
    <td className={cn("px-4 py-4 align-middle text-slate-700 dark:text-slate-200", className)}>
      {children}
    </td>
  );
}

import type { Metadata } from "next";

import { LoginForm } from "@/components/forms/login-form";

export const metadata: Metadata = {
  title: "Anmelden – Mouvin Personal",
};

export default async function LoginPage(props: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await props.searchParams;
  const nextRaw = params.next;
  const next =
    typeof nextRaw === "string" && nextRaw.startsWith("/") ? nextRaw : "/dashboard";

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 p-4 dark:bg-slate-950">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">
            Mouvin Personal
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Schicht- &amp; Rechnungssystem
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <LoginForm next={next} />
        </div>
      </div>
    </main>
  );
}

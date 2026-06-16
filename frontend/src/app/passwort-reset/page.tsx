import type { Metadata } from "next";

import {
  ConfirmResetForm,
  RequestResetForm,
} from "@/components/forms/password-reset-form";

export const metadata: Metadata = {
  title: "Passwort zurücksetzen – Schichtwerk",
};

export default async function PasswordResetPage(props: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await props.searchParams;
  const uid = typeof params.uid === "string" ? params.uid : "";
  const token = typeof params.token === "string" ? params.token : "";
  const hasLink = Boolean(uid && token);

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 p-4 dark:bg-slate-950">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">
            Passwort zurücksetzen
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Schichtwerk
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          {hasLink ? (
            <ConfirmResetForm uid={uid} token={token} />
          ) : (
            <RequestResetForm />
          )}
        </div>
      </div>
    </main>
  );
}

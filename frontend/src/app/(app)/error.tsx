"use client";

import { useEffect } from "react";

export default function AppError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // In der Browser-Konsole festhalten; Server-seitig greift das Logging/Monitoring.
    console.error(error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <h1 className="text-lg font-semibold text-slate-900 dark:text-white">
          Etwas ist schiefgelaufen
        </h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Die Seite konnte nicht geladen werden. Bitte versuchen Sie es erneut.
          Falls das Problem bestehen bleibt, laden Sie die Seite neu.
        </p>
        {error.digest && (
          <p className="mt-2 font-mono text-xs text-slate-400">
            Fehlercode: {error.digest}
          </p>
        )}
        <div className="mt-6 flex justify-center gap-3">
          <button
            onClick={reset}
            className="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
          >
            Erneut versuchen
          </button>
          <a
            href="/dashboard"
            className="inline-flex items-center rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
          >
            Zum Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}

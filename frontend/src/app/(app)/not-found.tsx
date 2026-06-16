export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-700 dark:bg-slate-800">
        <p className="text-4xl font-bold text-slate-300 dark:text-slate-600">404</p>
        <h1 className="mt-2 text-lg font-semibold text-slate-900 dark:text-white">
          Nicht gefunden
        </h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          Diese Seite oder dieser Datensatz existiert nicht oder gehört nicht zu
          Ihrer Organisation.
        </p>
        <div className="mt-6 flex justify-center">
          <a
            href="/dashboard"
            className="inline-flex items-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500"
          >
            Zum Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}

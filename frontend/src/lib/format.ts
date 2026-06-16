/** Formatierungshelfer für die deutsche Darstellung (de-DE). */

const eur = new Intl.NumberFormat("de-DE", {
  style: "currency",
  currency: "EUR",
});

const dateFmt = new Intl.DateTimeFormat("de-DE", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
});

const dateTimeFmt = new Intl.DateTimeFormat("de-DE", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

/** Wandelt einen DRF-Decimal-String/Number in einen Euro-Betrag um. */
export function formatEuro(value: string | number | null | undefined): string {
  const n = typeof value === "string" ? Number(value) : value;
  if (n === null || n === undefined || Number.isNaN(n)) return "–";
  return eur.format(n);
}

/** Stunden als deutsche Dezimalzahl mit „h“. */
export function formatHours(value: string | number | null | undefined): string {
  const n = typeof value === "string" ? Number(value) : value;
  if (n === null || n === undefined || Number.isNaN(n)) return "–";
  return `${n.toLocaleString("de-DE", { maximumFractionDigits: 2 })} h`;
}

/** Prozentwert (DRF-String) als „25 %“. */
export function formatPercent(value: string | number | null | undefined): string {
  const n = typeof value === "string" ? Number(value) : value;
  if (n === null || n === undefined || Number.isNaN(n)) return "–";
  return `${n.toLocaleString("de-DE", { maximumFractionDigits: 2 })} %`;
}

/** ISO-Datum (YYYY-MM-DD) → TT.MM.JJJJ. */
export function formatDate(value: string | null | undefined): string {
  if (!value) return "–";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return dateFmt.format(d);
}

/** ISO-Zeitstempel → TT.MM.JJJJ, HH:MM. */
export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "–";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return dateTimeFmt.format(d);
}

/** Zeit „HH:MM:SS“ → „HH:MM“. */
export function formatTime(value: string | null | undefined): string {
  if (!value) return "–";
  return value.slice(0, 5);
}

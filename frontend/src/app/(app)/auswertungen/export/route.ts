import { NextRequest } from "next/server";

import { proxyDownload } from "@/lib/download";

/** CSV-Export "Umsatz je Kunde" – reicht den Zeitraum (from/to) ans Backend durch. */
export async function GET(request: NextRequest) {
  const query = new URLSearchParams(request.nextUrl.searchParams);
  query.set("download", "csv");
  return proxyDownload("/reports/", query);
}

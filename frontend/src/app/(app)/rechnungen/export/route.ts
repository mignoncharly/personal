import { NextRequest } from "next/server";

import { proxyDownload } from "@/lib/download";

/** CSV-Export der (gefilterten) Rechnungen – reicht aktive Filter ans Backend durch. */
export async function GET(request: NextRequest) {
  return proxyDownload("/invoices/export/", request.nextUrl.searchParams);
}

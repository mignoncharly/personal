import { NextRequest } from "next/server";

import { proxyDownload } from "@/lib/download";

/** CSV-Export der (gefilterten) Schichten – reicht aktive Filter ans Backend durch. */
export async function GET(request: NextRequest) {
  return proxyDownload("/shifts/export/", request.nextUrl.searchParams);
}

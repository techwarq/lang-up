import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";

export function GET() {
  return NextResponse.json({
    wsUrl: process.env.BACKEND_WS_URL ?? "ws://localhost:8765",
  });
}

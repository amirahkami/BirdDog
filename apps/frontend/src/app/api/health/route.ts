const apiBaseUrl = process.env.API_INTERNAL_URL ?? "http://api:8000";

export const dynamic = "force-dynamic";

export async function GET() {
  try {
    const response = await fetch(`${apiBaseUrl}/health`, { cache: "no-store" });
    const body = await response.text();

    return new Response(body, {
      status: response.status,
      headers: { "content-type": "application/json" },
    });
  } catch {
    return Response.json(
      { status: "unavailable", database: "error" },
      { status: 503 },
    );
  }
}

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request) {
  try {
    const body = await request.json();
    const res = await fetch(`${BACKEND_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: body.message }),
    });
    if (!res.ok) {
      return Response.json(
        { answer: "Backend is not available. Make sure the Python server is running.", sources: [] },
        { status: 200 }
      );
    }
    const data = await res.json();
    return Response.json(data);
  } catch {
    return Response.json(
      { answer: "Could not connect to the backend. Run the Python server first.", sources: [] },
      { status: 200 }
    );
  }
}

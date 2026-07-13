# ADR 0002: Server-Sent Events

Use Server-Sent Events for one-way live state updates because the client only needs renderable state snapshots from the server. A polling fallback remains required for browsers or proxies where SSE is unavailable.

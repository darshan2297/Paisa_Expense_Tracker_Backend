"""Developer portal served at GET /."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from fastapi import APIRouter, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import HTMLResponse

from app.core.config import get_settings

portal_router = APIRouter(include_in_schema=False)


def _build_endpoint_groups(app: Any) -> list[dict[str, Any]]:
    schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for path, methods in schema.get("paths", {}).items():
        for method, detail in methods.items():
            if method.startswith("x-"):
                continue
            tags = detail.get("tags") or ["other"]
            tag = tags[0]
            grouped[tag].append(
                {
                    "method": method.upper(),
                    "path": path,
                    "summary": detail.get("summary") or "",
                }
            )
    return [
        {"tag": tag, "endpoints": sorted(eps, key=lambda e: e["path"])}
        for tag, eps in sorted(grouped.items())
    ]


@portal_router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def developer_portal(request: Request) -> HTMLResponse:
    settings = get_settings()
    groups = _build_endpoint_groups(request.app)
    total_endpoints = sum(len(g["endpoints"]) for g in groups)
    env_label = settings.ENVIRONMENT.upper()
    html = _PORTAL_HTML.format(
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=env_label,
        env_lower=settings.ENVIRONMENT,
        total_endpoints=total_endpoints,
        endpoint_groups=_render_groups(groups),
        flower_link=(
            '<a class="card" href="http://localhost:5555" target="_blank" rel="noopener">'
            "<h3>Celery Monitor</h3>"
            "<p>Flower dashboard (dev only). Run <code>celery -A app.worker.celery_app flower</code>.</p>"
            "</a>"
            if settings.ENVIRONMENT == "dev"
            else ""
        ),
    )
    return HTMLResponse(content=html)


def _render_groups(groups: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for group in groups[:8]:
        pills = "".join(
            f'<span class="pill pill-{ep["method"].lower()}">{ep["method"]} {ep["path"]}</span>'
            for ep in group["endpoints"][:6]
        )
        extra = len(group["endpoints"]) - 6
        if extra > 0:
            pills += f'<span class="pill pill-more">+ {extra} more</span>'
        parts.append(
            f'<div class="surface-group"><div class="surface-tag">{group["tag"]}</div><div class="pills">{pills}</div></div>'
        )
    remaining = sum(len(g["endpoints"]) for g in groups[8:])
    if remaining:
        parts.append(f'<div class="surface-more">+ {remaining} more endpoints — <a href="/docs">/docs</a></div>')
    return "\n".join(parts)


_PORTAL_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{app_name}</title>
  <style>
    :root {{
      --bg: #0f0e0c;
      --surface: #1a1814;
      --border: #2a2620;
      --text: #f4f2ef;
      --muted: #9a9288;
      --accent: #e8872a;
      --green: #3ecf8e;
      --get: #3ecf8e;
      --post: #e8872a;
      --patch: #5b54d6;
      --delete: #e05c4b;
      --put: #5b54d6;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: "Plus Jakarta Sans", system-ui, sans-serif;
      background: radial-gradient(ellipse at top, #1f1a14 0%, var(--bg) 55%);
      color: var(--text);
      min-height: 100vh;
      padding: 48px 24px 80px;
    }}
    .wrap {{ max-width: 1100px; margin: 0 auto; }}
    .brand {{ display: flex; align-items: center; gap: 16px; margin-bottom: 12px; }}
    .logo {{
      width: 44px; height: 44px; border-radius: 12px;
      background: linear-gradient(135deg, #f0a030, #c45e12);
      display: grid; place-items: center; font-size: 22px;
    }}
    h1 {{ font-size: 2rem; color: var(--accent); letter-spacing: -0.02em; }}
    .subtitle {{ color: var(--muted); margin-top: 8px; font-size: 0.95rem; }}
    .badge {{
      display: inline-block; margin-top: 14px; padding: 6px 14px;
      border-radius: 999px; border: 1px solid var(--border);
      background: var(--surface); color: var(--accent); font-size: 0.8rem;
      font-weight: 700; letter-spacing: 0.06em;
    }}
    .status {{
      margin: 28px 0; padding: 12px 16px; border-radius: 12px;
      background: var(--surface); border: 1px solid var(--border);
      display: flex; align-items: center; gap: 10px; font-size: 0.92rem;
    }}
    .dot {{ width: 10px; height: 10px; border-radius: 50%; background: var(--green); }}
    .section-title {{
      margin: 32px 0 16px; font-size: 0.75rem; letter-spacing: 0.14em;
      text-transform: uppercase; color: var(--muted);
    }}
    .grid {{
      display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 14px;
    }}
    .card {{
      display: block; text-decoration: none; color: inherit;
      background: var(--surface); border: 1px solid var(--border);
      border-radius: 16px; padding: 20px; transition: border-color 0.15s;
    }}
    .card:hover {{ border-color: #4a4338; }}
    .card h3 {{ font-size: 1rem; margin-bottom: 8px; }}
    .card p {{ color: var(--muted); font-size: 0.86rem; line-height: 1.5; }}
    .card code {{ color: #d4cbbf; font-size: 0.8rem; }}
    .surface {{ background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px; }}
    .surface-group {{ margin-bottom: 16px; }}
    .surface-tag {{
      font-size: 0.72rem; letter-spacing: 0.12em; text-transform: uppercase;
      color: var(--muted); margin-bottom: 10px;
    }}
    .pills {{ display: flex; flex-wrap: wrap; gap: 8px; }}
    .pill {{
      font-family: ui-monospace, monospace; font-size: 0.72rem;
      padding: 6px 10px; border-radius: 8px; border: 1px solid var(--border);
      background: #12100d;
    }}
    .pill-get {{ color: var(--get); border-color: #1e3d2f; }}
    .pill-post {{ color: var(--post); border-color: #3d2a14; }}
    .pill-patch, .pill-put {{ color: var(--patch); border-color: #2a2850; }}
    .pill-delete {{ color: var(--delete); border-color: #3d2018; }}
    .pill-more {{ color: var(--muted); }}
    .surface-more {{ margin-top: 12px; color: var(--muted); font-size: 0.85rem; }}
    .surface-more a {{ color: var(--accent); }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="brand">
      <div class="logo">₹</div>
      <div>
        <h1>{app_name}</h1>
        <p class="subtitle">Production-grade async API — FastAPI · Python 3.13 · PostgreSQL · Redis · Celery</p>
        <span class="badge">v{version} · {environment}</span>
      </div>
    </div>
    <div class="status">
      <span class="dot"></span>
      <span>All systems operational — {app_name} is running on <strong>{env_lower}</strong></span>
    </div>
    <div class="section-title">Developer Portal</div>
    <div class="grid">
      <a class="card" href="/docs"><h3>Swagger UI</h3><p>Interactive API explorer with live Try-it-out.</p></a>
      <a class="card" href="/redoc"><h3>ReDoc</h3><p>Clean, readable API reference documentation.</p></a>
      <a class="card" href="/openapi.json"><h3>OpenAPI JSON</h3><p>Raw OpenAPI 3.x specification for Postman or Insomnia.</p></a>
      <a class="card" href="/api/v1/health/live"><h3>Health Live</h3><p>Liveness — process up, version, environment.</p></a>
      <a class="card" href="/api/v1/health/ready"><h3>Readiness Check</h3><p>PostgreSQL + Redis connectivity.</p></a>
      {flower_link}
    </div>
    <div class="section-title">API Surface · {total_endpoints} endpoints</div>
    <div class="surface">{endpoint_groups}</div>
  </div>
</body>
</html>"""

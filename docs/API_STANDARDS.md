# Backend — API Standards

## Standard Response Envelope

Every JSON response (success or error), via `ResponseEnvelopeMiddleware`:
```json
{"success": true, "status_code": 200, "data": {...}, "message": "...", "errors": null}
```
Route handlers return plain data — never construct the envelope by hand.

## URL Conventions

- Versioned: `/api/v1/...`.
- Collections: `/api/v1/transactions`. Items: `/api/v1/transactions/{id}`. Actions as
  sub-resources: `/api/v1/bills/{id}/pay` — never a verb in the path.

## HTTP Status Codes

| Scenario | Code |
|---|---|
| Successful read/update/delete | 200 |
| Resource created | 201 |
| Validation error (Pydantic) | 422 |
| Business rule violation (`ConflictError`) | 409 |
| Auth required | 401 |
| Insufficient permission (`ForbiddenError`) | 403 |
| Not found (`NotFoundError`) | 404 |
| Rate limited | 429 |
| Unhandled error | 500 |

## Pagination

Use the `PageParams` dependency (`app/core/pagination.py`) on every list endpoint:
`page` (default 1), `size` (default 20, capped). Response shape:
```json
{"data": [...], "total": 100, "page": 1, "size": 20, "pages": 5}
```
No list endpoint may return an unbounded collection.

## Filtering & Sorting

Query params named for the field (`?category=food&type=expense`); sorting via
`?sort=-date` (`-` prefix = descending).

## Rate Limiting

`app/middleware/rate_limit.py` exposes the default limiter (`RATE_LIMIT_DEFAULT` env
var, `100/minute` default) plus a `strict_limit` decorator for sensitive endpoints
(apply to auth routes once F1 ships). In-memory backend — fails open, never 500s the
API if the limiter itself has a problem.

## Versioning

Current: `/api/v1/`. A breaking change (removed/renamed field, changed type, changed
URL) requires `/api/v2/...` alongside `/v1` for at least one release cycle — additive
changes (new optional fields) are never breaking.

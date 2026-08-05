"""HTML + plain-text templates for Paisa reminder emails."""

from __future__ import annotations

KIND_LABELS = {
    "bill_due": "Bill reminder",
    "fixed_due": "EMI / commitment",
    "policy_renewal": "Policy renewal",
}


def render_reminder_email(
    *,
    recipient_name: str,
    kind: str,
    title: str,
    body: str,
    amount_display: str | None = None,
    due_label: str | None = None,
    urgency: str | None = None,
) -> tuple[str, str]:
    """Return (html, text) for a reminder email."""
    kind_label = KIND_LABELS.get(kind, "Reminder")
    first_name = (recipient_name or "there").strip().split()[0] or "there"

    meta_rows = ""
    if amount_display:
        meta_rows += f"""
            <tr>
              <td style="padding:10px 0;border-bottom:1px solid #e8ebe9;color:#5c6b63;font-size:13px;letter-spacing:0.04em;text-transform:uppercase;">Amount</td>
              <td align="right" style="padding:10px 0;border-bottom:1px solid #e8ebe9;color:#0f1f17;font-size:20px;font-weight:700;font-variant-numeric:tabular-nums;">{amount_display}</td>
            </tr>"""
    if due_label:
        meta_rows += f"""
            <tr>
              <td style="padding:10px 0;border-bottom:1px solid #e8ebe9;color:#5c6b63;font-size:13px;letter-spacing:0.04em;text-transform:uppercase;">Due</td>
              <td align="right" style="padding:10px 0;border-bottom:1px solid #e8ebe9;color:#0f1f17;font-size:15px;font-weight:600;">{due_label}</td>
            </tr>"""
    if urgency:
        meta_rows += f"""
            <tr>
              <td style="padding:10px 0;color:#5c6b63;font-size:13px;letter-spacing:0.04em;text-transform:uppercase;">When</td>
              <td align="right" style="padding:10px 0;color:#1f6b4a;font-size:15px;font-weight:600;">{urgency}</td>
            </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
</head>
<body style="margin:0;padding:0;background:#f3f6f4;font-family:Georgia,'Times New Roman',serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f6f4;padding:32px 16px;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#ffffff;border:1px solid #d8e4de;border-radius:4px;overflow:hidden;">
          <tr>
            <td style="background:linear-gradient(135deg,#0f1f17 0%,#1f6b4a 100%);padding:28px 32px;">
              <p style="margin:0 0 6px;color:#a8cbb8;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:12px;letter-spacing:0.14em;text-transform:uppercase;">Paisa</p>
              <h1 style="margin:0;color:#ffffff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:22px;font-weight:650;line-height:1.3;">{kind_label}</h1>
            </td>
          </tr>
          <tr>
            <td style="padding:32px;">
              <p style="margin:0 0 16px;color:#3d4a43;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:15px;line-height:1.55;">
                Hi {first_name},
              </p>
              <p style="margin:0 0 24px;color:#0f1f17;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:16px;line-height:1.55;font-weight:600;">
                {title}
              </p>
              <p style="margin:0 0 24px;color:#3d4a43;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:15px;line-height:1.6;">
                {body}
              </p>
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f7faf8;border:1px solid #e0e8e3;border-radius:4px;padding:4px 20px;margin:0 0 28px;">
                {meta_rows}
              </table>
              <p style="margin:0;color:#7a8a82;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:13px;line-height:1.5;">
                Open Paisa to mark this paid or adjust your reminder lead days.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:18px 32px;border-top:1px solid #e8ebe9;background:#fafcfb;">
              <p style="margin:0;color:#9aa8a0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:12px;line-height:1.5;">
                You’re receiving this because reminders are enabled on your Paisa account.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    text_lines = [
        f"Paisa — {kind_label}",
        "",
        f"Hi {first_name},",
        "",
        title,
        body,
    ]
    if amount_display:
        text_lines.extend(["", f"Amount: {amount_display}"])
    if due_label:
        text_lines.append(f"Due: {due_label}")
    if urgency:
        text_lines.append(f"When: {urgency}")
    text_lines.extend(["", "Open Paisa to mark this paid or adjust your reminder lead days."])
    text = "\n".join(text_lines)
    return html, text

"""FastAPI email routes — Phase E2/E3.

Endpoints:
  GET  /api/email/inbox           — Check Zoho inbox
  GET  /api/email/queue           — List the email approval queue
  POST /api/email/queue/{id}/approve — Approve a queued email (status → APPROVED)
  POST /api/email/queue/{id}/cancel  — Cancel a queued email (status → CANCELLED)
  GET  /api/email/audit           — View the audit log
  GET  /api/email/status          — Kill switch + rate limit status (no auth needed)

Safety notes:
- Approving moves status to APPROVED only.  Actual sending requires a separate
  implementation (Phase E4) that checks kill switch + rate limits before send.
- The kill switch is read from settings.yaml at request time, not cached.
- All approve/cancel actions are logged to email_audit_log.
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter()

# ---------------------------------------------------------------------------
# Inbox read
# ---------------------------------------------------------------------------


@router.get("/inbox")
def get_inbox(
    days: int = Query(7, ge=1, le=30, description="Days to look back"),
    contacts_only: bool = Query(
        True, description="Only emails from known CRM contacts"
    ),
):
    """Check the Zoho inbox and return recent emails."""
    try:
        from tools.email.zoho_reader import check_inbox

        result = check_inbox(days_back=days, from_contacts_only=contacts_only)
        if "error" in result:
            raise HTTPException(status_code=503, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Inbox check failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Queue management
# ---------------------------------------------------------------------------


@router.get("/queue")
def list_queue(
    status: Optional[str] = Query(
        None,
        description=(
            "Filter by status: PENDING_APPROVAL, APPROVED, SENDING, "
            "SENT, FAILED, CANCELLED"
        ),
    ),
    limit: int = Query(50, ge=1, le=200),
):
    """Return queued emails, optionally filtered by status."""
    try:
        from tools.email.safety import get_queue

        rows = get_queue(status=status, limit=limit)
        # Truncate body in list view to keep response lean
        for row in rows:
            if row.get("body") and len(row["body"]) > 300:
                row["body"] = row["body"][:300] + "..."
        return {"queue": rows, "total": len(rows)}
    except Exception as exc:
        logger.exception("List queue failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/queue/{queue_id}/approve")
def approve_email(queue_id: int):
    """Approve a queued email — moves status to APPROVED.

    Note: approval does NOT send the email.  Sending requires Phase E4
    implementation with full kill-switch and rate-limit checks.
    """
    try:
        from tools.email.safety import get_queue, update_queue_status

        rows = get_queue(limit=1)  # just to initialize schema
        # Fetch the specific row to validate it exists
        from tools.email.safety import _get_db

        conn = _get_db()
        try:
            row = conn.execute(
                "SELECT id, status, from_account FROM email_queue WHERE id = ?",
                (queue_id,),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            raise HTTPException(
                status_code=404, detail=f"Queue entry {queue_id} not found"
            )

        current_status = row["status"]
        if current_status not in ("PENDING_APPROVAL",):
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Cannot approve email in status {current_status!r}. "
                    "Only PENDING_APPROVAL emails can be approved."
                ),
            )

        result = update_queue_status(
            queue_id=queue_id, new_status="APPROVED", actor="hermann"
        )
        return {
            "approved": True,
            "queue_id": queue_id,
            "status": result["status"],
            "note": (
                "Email approved. Sending requires Phase E4 implementation "
                "with kill-switch and rate-limit enforcement."
            ),
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Approve failed for queue_id=%s", queue_id)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/queue/{queue_id}/cancel")
def cancel_email(queue_id: int):
    """Cancel a queued email — moves status to CANCELLED."""
    try:
        from tools.email.safety import _get_db, update_queue_status

        conn = _get_db()
        try:
            row = conn.execute(
                "SELECT id, status FROM email_queue WHERE id = ?",
                (queue_id,),
            ).fetchone()
        finally:
            conn.close()

        if row is None:
            raise HTTPException(
                status_code=404, detail=f"Queue entry {queue_id} not found"
            )

        if row["status"] in ("SENT", "CANCELLED"):
            raise HTTPException(
                status_code=409,
                detail=f"Email is already in final status: {row['status']!r}",
            )

        result = update_queue_status(
            queue_id=queue_id, new_status="CANCELLED", actor="hermann"
        )
        return {"cancelled": True, "queue_id": queue_id, "status": result["status"]}

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Cancel failed for queue_id=%s", queue_id)
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------


@router.get("/audit")
def get_audit(
    queue_id: Optional[int] = Query(
        None, description="Filter to a specific email queue entry"
    ),
    limit: int = Query(100, ge=1, le=500),
):
    """Return audit log entries, newest first."""
    try:
        from tools.email.safety import get_audit_log

        entries = get_audit_log(queue_id=queue_id, limit=limit)
        return {"audit_log": entries, "total": len(entries)}
    except Exception as exc:
        logger.exception("Audit log fetch failed")
        raise HTTPException(status_code=500, detail=str(exc))


# ---------------------------------------------------------------------------
# Status / health check
# ---------------------------------------------------------------------------


@router.get("/status")
def email_status():
    """Return current kill-switch state and rate-limit counters.

    Safe to call without credentials — useful for dashboard health display.
    """
    try:
        from tools.email.safety import check_rate_limit, is_send_enabled

        send_enabled = is_send_enabled()
        com_rate = check_rate_limit("com")
        co_rate = check_rate_limit("co")

        return {
            "automated_send_enabled": send_enabled,
            "com": {
                "account": "hermann@aitourpilot.com",
                "auto_send": False,  # NEVER — code-level constraint
                "rate_limit": com_rate,
            },
            "co": {
                "account": "hermann@kudlich.co",
                "auto_send": send_enabled,  # only if kill switch is ON
                "rate_limit": co_rate,
            },
            "safety_note": (
                ".com account never auto-sends regardless of kill switch. "
                "All emails require manual approval via the queue."
            ),
        }
    except Exception as exc:
        logger.exception("Email status check failed")
        raise HTTPException(status_code=500, detail=str(exc))

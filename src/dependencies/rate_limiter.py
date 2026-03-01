"""
Per-user rate limiting for review submission requests (issue #663).

Uses an in-memory rolling window to track submissions per user.
Connectors (users with platform_* roles) bypass rate limiting as they use
a separate workflow for systematic data migrations.
"""

import datetime
import logging
from collections import defaultdict, deque

from fastapi import Depends, HTTPException, status

from authentication import KeycloakUser, get_user_or_raise
from config import RATE_LIMIT_CONFIG

logger = logging.getLogger(__name__)

# In-memory store: maps user subject_identifier -> deque of submission timestamps
_submission_timestamps: dict[str, deque[datetime.datetime]] = defaultdict(deque)

MAX_SUBMISSIONS: int = RATE_LIMIT_CONFIG.get("max_submissions_per_user", 10)
WINDOW_SECONDS: int = RATE_LIMIT_CONFIG.get("submission_window_seconds", 3600)


def _clean_expired_entries(user_id: str) -> None:
    """Remove timestamps that fall outside the current rolling window."""
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
        seconds=WINDOW_SECONDS
    )
    timestamps = _submission_timestamps[user_id]
    while timestamps and timestamps[0] < cutoff:
        timestamps.popleft()


def check_submission_rate_limit(
    user: KeycloakUser = Depends(get_user_or_raise),
) -> None:
    """
    FastAPI dependency that enforces per-user rate limiting on review submissions.

    Connectors (platform roles) are exempt — they use the connector workflow
    designed for systematic uploads (see issue #663).

    Raises:
        HTTPException 429 if the user has exceeded max_submissions_per_user
        within the submission_window_seconds rolling window.
    """
    if user.is_connector:
        return  # connectors bypass rate limiting

    user_id = user._subject_identifier
    _clean_expired_entries(user_id)

    timestamps = _submission_timestamps[user_id]
    if len(timestamps) >= MAX_SUBMISSIONS:
        window_minutes = WINDOW_SECONDS // 60
        logger.warning(
            f"Rate limit exceeded for user {user.name!r}: "
            f"{len(timestamps)}/{MAX_SUBMISSIONS} submissions in {window_minutes} min window."
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Rate limit exceeded: you may submit at most {MAX_SUBMISSIONS} "
                f"review requests per {window_minutes} minutes. "
                "Please try again later."
            ),
        )

    # Record this submission timestamp
    timestamps.append(datetime.datetime.now(datetime.timezone.utc))

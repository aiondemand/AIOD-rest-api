"""Rate limiting for asset uploads.

Uses database-backed rolling time windows to limit user uploads. Connectors are
exempted. Rate limits are global across all asset types.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, UTC

from fastapi import HTTPException, status
from sqlmodel import select
from sqlalchemy import func

from authentication import KeycloakUser
from config import CONFIG
from database.model.access.upload_log import AssetUploadLog
from database.session import DbSession

logger = logging.getLogger(__file__)


def _get_rate_limit_config() -> tuple[bool, int, int]:
    """Extract rate limit configuration.

    Returns:
        Tuple of (enabled, uploads_per_window, window_seconds)
    """
    rate_config = CONFIG.get("rate_limit", {})
    enabled = bool(rate_config.get("enabled", False))
    uploads_per_window = int(rate_config.get("uploads_per_window", 0) or 0)
    window_seconds = int(rate_config.get("window_seconds", 0) or 0)
    return enabled, uploads_per_window, window_seconds


def enforce_upload_rate_limit(user: KeycloakUser | None, resource_type: str) -> None:
    """Enforce upload rate limit for the given user.

    Args:
        user: Authenticated user or None
        resource_type: Asset type being uploaded (for logging only)

    Raises:
        HTTPException: 401 if user is not authenticated, 429 if rate limit exceeded
    """
    enabled, uploads_per_window, window_seconds = _get_rate_limit_config()
    if not enabled or uploads_per_window <= 0 or window_seconds <= 0:
        return

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required to upload assets.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Explicitly bypass rate limiting for connectors (bulk data migration services)
    if user.is_connector:
        return

    now = datetime.now(UTC)
    window_start = now - timedelta(seconds=window_seconds)

    with DbSession() as session:
        # NOTE: Not strictly atomic under high concurrency. Minor bursts above limit are
        # acceptable and common in DB-backed rate limiters without distributed locks.
        count = session.exec(
            select(func.count(AssetUploadLog.id)).where(
                AssetUploadLog.user_identifier == user._subject_identifier,
                AssetUploadLog.created_at >= window_start,
            )
        ).one()
        if count >= uploads_per_window:
            # Calculate precise retry timing (only executed on limit breach)
            oldest = session.exec(
                select(AssetUploadLog.created_at)
                .where(
                    AssetUploadLog.user_identifier == user._subject_identifier,
                    AssetUploadLog.created_at >= window_start,
                )
                .order_by(AssetUploadLog.created_at.asc())
                .limit(1)
            ).first()
            retry_after = window_seconds
            if oldest:
                retry_after = max(
                    0, int(window_seconds - (now - oldest).total_seconds())
                )

            logger.warning(
                "Upload rate limit exceeded: user=%s resource_type=%s count=%s window_seconds=%s",
                user._subject_identifier,
                resource_type,
                count,
                window_seconds,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    "Upload rate limit exceeded: max "
                    f"{uploads_per_window} uploads per {window_seconds} seconds. "
                    f"Retry after {retry_after} seconds."
                ),
                headers={"Retry-After": str(retry_after)},
            )


def record_successful_upload(user: KeycloakUser | None, resource_type: str) -> None:
    """Record a successful upload for rate limiting.

    Args:
        user: Authenticated user or None
        resource_type: Asset type that was uploaded
    """
    enabled, uploads_per_window, window_seconds = _get_rate_limit_config()
    if not enabled or uploads_per_window <= 0 or window_seconds <= 0:
        return

    if user is None or user.is_connector:
        return

    try:
        with DbSession() as session:
            session.add(
                AssetUploadLog(
                    user_identifier=user._subject_identifier,
                    resource_type=resource_type,
                )
            )
            session.commit()
    except Exception as exc:
        # Graceful degradation: failures don't block the upload pipeline
        logger.error("Failed to record upload for rate limiting: %s", exc)

"""
Tests for per-user rate limiting on review submission requests (issue #663).
"""

import datetime
from collections import deque

import pytest
from fastapi import HTTPException

from authentication import KeycloakUser
from dependencies.rate_limiter import (
    MAX_SUBMISSIONS,
    WINDOW_SECONDS,
    _submission_timestamps,
    check_submission_rate_limit,
)


def _make_user(
    subject_id: str = "user-001",
    name: str = "testuser",
    roles: set[str] | None = None,
) -> KeycloakUser:
    if roles is None:
        roles = {"offline_access", "uma_authorization", "default-roles-aiod"}
    return KeycloakUser(name=name, roles=roles, _subject_identifier=subject_id)


@pytest.fixture(autouse=True)
def _clear_rate_limit_state():
    """Ensure a clean rate limiter state for every test."""
    _submission_timestamps.clear()
    yield
    _submission_timestamps.clear()


class TestSubmissionRateLimit:

    def test_allows_submissions_within_limit(self):
        """Submissions at or below the limit should pass."""
        user = _make_user()
        for _ in range(MAX_SUBMISSIONS):
            check_submission_rate_limit(user)
        assert len(_submission_timestamps[user._subject_identifier]) == MAX_SUBMISSIONS

    def test_rejects_submission_over_limit(self):
        """One submission beyond the limit must raise HTTP 429."""
        user = _make_user()
        for _ in range(MAX_SUBMISSIONS):
            check_submission_rate_limit(user)

        with pytest.raises(HTTPException) as exc_info:
            check_submission_rate_limit(user)
        assert exc_info.value.status_code == 429
        assert "Rate limit exceeded" in exc_info.value.detail

    def test_allows_after_window_expires(self):
        """Submissions from outside the window should be cleaned and new ones allowed."""
        user = _make_user()
        expired = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            seconds=WINDOW_SECONDS + 1
        )
        _submission_timestamps[user._subject_identifier] = deque(
            [expired] * MAX_SUBMISSIONS
        )
        # All expired — should succeed
        check_submission_rate_limit(user)
        assert len(_submission_timestamps[user._subject_identifier]) == 1

    def test_connector_bypasses_rate_limit(self):
        """Users with platform_* roles (connectors) are never rate-limited."""
        connector = _make_user(
            subject_id="connector-001",
            roles={"platform_huggingface", "default-roles-aiod"},
        )
        for _ in range(MAX_SUBMISSIONS + 5):
            check_submission_rate_limit(connector)
        assert "connector-001" not in _submission_timestamps

    def test_independent_counters_per_user(self):
        """Each user has an independent rate limit counter."""
        alice = _make_user(subject_id="alice", name="alice")
        bob = _make_user(subject_id="bob", name="bob")

        for _ in range(MAX_SUBMISSIONS):
            check_submission_rate_limit(alice)

        # Bob should still be free
        check_submission_rate_limit(bob)
        assert len(_submission_timestamps["bob"]) == 1

        # Alice should be blocked
        with pytest.raises(HTTPException) as exc_info:
            check_submission_rate_limit(alice)
        assert exc_info.value.status_code == 429

    def test_partial_expiry_keeps_recent_entries(self):
        """Expired entries are cleaned but recent ones are preserved."""
        user = _make_user()
        now = datetime.datetime.now(datetime.timezone.utc)
        expired = now - datetime.timedelta(seconds=WINDOW_SECONDS + 1)
        recent = now - datetime.timedelta(seconds=60)
        # 5 expired + 4 recent = 9 — under the limit
        _submission_timestamps[user._subject_identifier] = deque(
            [expired] * 5 + [recent] * 4
        )
        check_submission_rate_limit(user)
        # 5 expired cleaned, 4 recent + 1 new = 5
        assert len(_submission_timestamps[user._subject_identifier]) == 5

    def test_error_message_includes_limits(self):
        """The 429 detail must include the configured limit and window."""
        user = _make_user()
        for _ in range(MAX_SUBMISSIONS):
            check_submission_rate_limit(user)
        with pytest.raises(HTTPException) as exc_info:
            check_submission_rate_limit(user)
        assert str(MAX_SUBMISSIONS) in exc_info.value.detail
        assert str(WINDOW_SECONDS // 60) in exc_info.value.detail

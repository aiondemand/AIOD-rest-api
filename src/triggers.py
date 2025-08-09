from sqlalchemy import DDL
from sqlmodel import Session

BYPASS_REVIEW_TRIGGER_NAME: str = "PUBLISH_ON_CREATE"


def disable_review_process(session: Session) -> None:
    """Sets new entries to automatically be published, circumventing the review process."""
    session.execute(
        DDL(f"""
        CREATE TRIGGER IF NOT EXISTS {BYPASS_REVIEW_TRIGGER_NAME}
        BEFORE INSERT ON aiod_entry
        FOR EACH ROW
        BEGIN
            SET NEW.status = 'PUBLISHED';
        END;
    """)
    )


def enable_review_process(session: Session) -> None:
    """Drops the trigger created by `disable_review_process`"""
    session.execute(DDL(f"DROP TRIGGER IF EXISTS {BYPASS_REVIEW_TRIGGER_NAME};"))

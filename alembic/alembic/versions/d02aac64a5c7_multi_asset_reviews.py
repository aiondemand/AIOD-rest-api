"""multi_asset_reviews

Revision ID: d02aac64a5c7
Revises: 1fd9b6a162c4
Create Date: 2025-09-16 12:27:10.238574

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d02aac64a5c7"
down_revision: Union[str, None] = "1fd9b6a162c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # We use a nuclear approach as there are no reviews in the database anyway:
    op.drop_table("review")
    op.drop_table("submission")

    # We could leave it at the above an rely on SQLAlchemy to create the tables below.
    # However, this increases the complexity of the deployment so make it explicit:
    op.create_table(
        "submission",
        sa.Column("identifier", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("request_date", sa.DateTime(), nullable=False),
        sa.Column("comment", sa.String(256), nullable=False),
        sa.Column("requestee_identifier", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("identifier"),
        sa.ForeignKeyConstraint(
            ["requestee_identifier"],
            ["user.subject_identifier"],
            name="submission_ibfk_1",
            ondelete="SET NULL",
        ),
    )
    op.create_index("requestee_identifier", "submission", ["requestee_identifier"])

    op.create_table(
        "review",
        sa.Column("comment", sa.String(1800), nullable=False),
        sa.Column(
            "decision",
            sa.Enum("ACCEPTED", "REJECTED", "RETRACTED", name="review_decision"),
            nullable=True,
        ),
        sa.Column("identifier", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("decision_date", sa.DateTime(), nullable=False),
        sa.Column("reviewer_identifier", sa.String(255), nullable=False),
        sa.Column("submission_identifier", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("identifier"),
        sa.ForeignKeyConstraint(
            ["reviewer_identifier"], ["user.subject_identifier"], name="review_ibfk_1"
        ),
        sa.ForeignKeyConstraint(
            ["submission_identifier"], ["submission.identifier"], name="review_ibfk_2"
        ),
    )
    op.create_index("reviewer_identifier", "review", ["reviewer_identifier"])
    op.create_index("submission_identifier", "review", ["submission_identifier"])

    op.create_table(
        "asset_review",
        sa.Column("asset_identifier", sa.String(255), nullable=False),
        sa.Column("aiod_entry_identifier", sa.Integer(), nullable=False),
        sa.Column("review_identifier", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("aiod_entry_identifier", "review_identifier"),
        sa.ForeignKeyConstraint(
            ["aiod_entry_identifier"],
            ["aiod_entry.identifier"],
            name="asset_review_ibfk_1",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["review_identifier"],
            ["submission.identifier"],
            name="asset_review_ibfk_2",
            ondelete="CASCADE",
        ),
    )
    op.create_index("review_identifier", "asset_review", ["review_identifier"])


def downgrade() -> None:
    op.drop_table("review")
    op.drop_table("asset_review")
    op.drop_table("submission")

    # just start the server and the tables will be created automatically.

"""cascade delete ai resource

Revision ID: 8f9ac801a283
Revises: 95fa6a3c7eee
Create Date: 2025-10-30 14:10:21.536071

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8f9ac801a283"
down_revision: Union[str, None] = "95fa6a3c7eee"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def recreate_constraints(with_on_delete_cascade: bool):
    for table in ["part", "relevant"]:
        op.drop_constraint(
            f"ai_resource_{table}_link_ibfk_1", f"ai_resource_{table}_link", type_="foreignkey"
        )
        op.drop_constraint(
            f"ai_resource_{table}_link_ibfk_2", f"ai_resource_{table}_link", type_="foreignkey"
        )

        op.create_foreign_key(
            f"ai_resource_{table}_link_ibfk_1",
            f"ai_resource_{table}_link",
            "ai_resource",
            ["parent_identifier"],
            ["identifier"],
            onupdate="CASCADE",
            ondelete="CASCADE" if with_on_delete_cascade else None,
        )
        local_col = "child_identifier" if table == "part" else "relevant_identifier"
        op.create_foreign_key(
            f"ai_resource_{table}_link_ibfk_2",
            f"ai_resource_{table}_link",
            "ai_resource",
            [local_col],
            ["identifier"],
            onupdate="CASCADE",
            ondelete="CASCADE" if with_on_delete_cascade else None,
        )


def upgrade():
    recreate_constraints(with_on_delete_cascade=True)


def downgrade():
    recreate_constraints(with_on_delete_cascade=False)

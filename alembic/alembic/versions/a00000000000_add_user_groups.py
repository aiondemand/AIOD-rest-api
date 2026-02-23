"""add user groups

Revision ID: a00000000000
Revises: 8f9ac801a283
Create Date: 2026-02-23 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = 'a00000000000'
down_revision: Union[str, None] = '8f9ac801a283'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create user_group table
    op.create_table(
        'user_group',
        sa.Column('identifier', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('identifier'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_user_group_name'), 'user_group', ['name'], unique=True)

    # Create user_group_membership table
    op.create_table(
        'user_group_membership',
        sa.Column('user_group_identifier', sa.Integer(), nullable=False),
        sa.Column('user_identifier', sa.String(length=255), nullable=False),
        sa.ForeignKeyConstraint(['user_group_identifier'], ['user_group.identifier'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_identifier'], ['user.subject_identifier'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_group_identifier', 'user_identifier')
    )

    # Note: SQLite vs MySQL differences. Since tests use SQLModel.metadata.create_all() for SQLite,
    # this Alembic script is primarily for MySQL in the deployed environment.
    conn = op.get_bind()
    insp = Inspector.from_engine(conn)  # type: ignore
    
    # We need to drop the existing primary key from permission table.
    # In MySQL, we can just drop the PRIMARY KEY.
    if conn.dialect.name == "mysql":
        op.drop_constraint('PRIMARY', 'permission', type_='primary')
    else:
        # SQLite doesn't support dropping primary keys. We'll rebuild via batch.
        with op.batch_alter_table('permission', naming_convention={'pk': 'pk_%(table_name)s'}) as batch_op:
            pass # Pk dropping not natively supported in SQLite batch without recreate, but SQLModel create_all bypasses this in tests.

    # Alter permission table
    op.add_column('permission', sa.Column('identifier', sa.Integer(), nullable=True))
    op.add_column('permission', sa.Column('user_group_identifier', sa.Integer(), nullable=True))

    # set existing identifier? We cannot easily backfill autoincrement in place, but we can 
    # make it primary key and auto_increment.
    if conn.dialect.name == "mysql":
        op.alter_column('permission', 'identifier', existing_type=sa.Integer(), nullable=False, autoincrement=True)
        op.create_primary_key('pk_permission', 'permission', ['identifier'])
        op.alter_column('permission', 'identifier', existing_type=sa.Integer(), server_default=sa.text("AUTO_INCREMENT"))
        # alter user_identifier to be nullable
        op.alter_column('permission', 'user_identifier', existing_type=sa.String(length=255), nullable=True)
    else:
        # Recreating for sqlite if needed
        pass

    op.create_foreign_key('fk_permission_user_group', 'permission', 'user_group', ['user_group_identifier'], ['identifier'], ondelete='CASCADE')
    op.create_unique_constraint('uq_permission_aiod_entry_user_group', 'permission', ['aiod_entry_identifier', 'user_identifier', 'user_group_identifier'])


def downgrade() -> None:
    op.drop_constraint('uq_permission_aiod_entry_user_group', 'permission', type_='unique')
    op.drop_constraint('fk_permission_user_group', 'permission', type_='foreignkey')
    
    conn = op.get_bind()
    if conn.dialect.name == "mysql":
        op.alter_column('permission', 'user_identifier', existing_type=sa.String(length=255), nullable=False)
        op.drop_constraint('pk_permission', 'permission', type_='primary')
        op.create_primary_key('PRIMARY', 'permission', ['aiod_entry_identifier', 'user_identifier'])
    
    op.drop_column('permission', 'user_group_identifier')
    op.drop_column('permission', 'identifier')
    
    op.drop_table('user_group_membership')
    op.drop_index(op.f('ix_user_group_name'), table_name='user_group')
    op.drop_table('user_group')

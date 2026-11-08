"""Add user authentication without removing existing users.

Revision ID: 090_authentication
Revises: 82678d126065
"""
from alembic import op
import sqlalchemy as sa

revision = '090_authentication'
down_revision = '82678d126065'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.add_column(sa.Column('email', sa.String(254), nullable=True))
        batch_op.add_column(sa.Column('password_hash', sa.String(256), nullable=True))
        batch_op.add_column(sa.Column('confirmed', sa.Boolean(), nullable=False,
                                      server_default=sa.false()))
        batch_op.create_index('ix_users_email', ['email'], unique=True)


def downgrade():
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_index('ix_users_email')
        batch_op.drop_column('confirmed')
        batch_op.drop_column('password_hash')
        batch_op.drop_column('email')

"""rename metadata columns to metadata_json

Revision ID: 0002_rename_metadata
Revises: 0001_create_audit_logs
Create Date: 2026-08-13 15:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_rename_metadata'
down_revision = '0001_create_audit_logs'
branch_labels = None
depends_on = None


def upgrade():
    # Use batch_alter_table to support SQLite
    with op.batch_alter_table('retrieval_records') as batch_op:
        batch_op.alter_column('metadata', new_column_name='metadata_json', existing_type=sa.Text(), nullable=True)

    with op.batch_alter_table('evidence') as batch_op:
        batch_op.alter_column('metadata', new_column_name='metadata_json', existing_type=sa.Text(), nullable=True)


def downgrade():
    with op.batch_alter_table('retrieval_records') as batch_op:
        batch_op.alter_column('metadata_json', new_column_name='metadata', existing_type=sa.Text(), nullable=True)

    with op.batch_alter_table('evidence') as batch_op:
        batch_op.alter_column('metadata_json', new_column_name='metadata', existing_type=sa.Text(), nullable=True)

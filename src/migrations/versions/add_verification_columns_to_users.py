"""add verification columns to users

Revision ID: add_verification_cols
Revises: 9543c00b6ede
Create Date: 2025-11-03 20:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_verification_cols'
down_revision = '9543c00b6ede'
branch_labels = None
depends_on = None


def upgrade():
    # Add verification_token and token_expires_at columns if they don't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='users' AND column_name='verification_token'
            ) THEN
                ALTER TABLE users ADD COLUMN verification_token VARCHAR(255);
            END IF;
            
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name='users' AND column_name='token_expires_at'
            ) THEN
                ALTER TABLE users ADD COLUMN token_expires_at TIMESTAMP;
            END IF;
        END $$;
    """)


def downgrade():
    # Remove the columns if migration is rolled back
    op.drop_column('users', 'token_expires_at')
    op.drop_column('users', 'verification_token')


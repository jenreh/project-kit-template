"""Bring the appkit-user schema up to 1.18 and retire the shared default admin.

Adds the password reset, password history and login throttle tables.

Projects generated before this revision seeded one admin account with the same
password hash everywhere. That account is deactivated if its password was never
changed. A password reset would not help, because anyone who knows the shared
password could perform it. Run `task admin:bootstrap` to create your own admin.

Revision ID: appkit_user_1_18
Revises: appkit_user
Create Date: 2026-11-02 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "appkit_user_1_18"
down_revision: str | None = "appkit_user"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column(
            "created",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    ]


def upgrade() -> None:
    op.create_table(
        "auth_password_reset_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=200), nullable=True),
        sa.Column("reset_type", sa.String(length=50), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["auth_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token"),
    )
    op.create_index(
        "idx_password_reset_tokens_token_expires",
        "auth_password_reset_tokens",
        ["token", "expires_at"],
    )
    op.create_index(
        "idx_password_reset_tokens_user_id_used",
        "auth_password_reset_tokens",
        ["user_id", "is_used"],
    )

    op.create_table(
        "auth_password_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("password_hash", sa.String(length=200), nullable=False),
        sa.Column(
            "changed_at", sa.DateTime(), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("change_reason", sa.String(length=50), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["auth_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "password_hash", name="uq_password_history_user_hash"
        ),
    )
    op.create_index(
        "idx_password_history_user_id_changed",
        "auth_password_history",
        ["user_id", "changed_at"],
    )

    op.create_table(
        "auth_password_reset_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=200), nullable=False),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "auth_login_throttle",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("failures", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_index(
        "idx_login_throttle_window_started",
        "auth_login_throttle",
        ["window_started_at"],
    )

    # Matches on the salt of the old seed, so an admin whose password was changed
    # stays active.
    op.execute(
        r"""
        UPDATE auth_users
        SET is_active = false, needs_password_reset = true
        WHERE email = 'admin'
          AND _password LIKE 'scrypt:32768:8:1$bIA8HVQhPyudwZyV$%'
        """
    )


def downgrade() -> None:
    op.drop_table("auth_login_throttle")
    op.drop_table("auth_password_reset_requests")
    op.drop_table("auth_password_history")
    op.drop_table("auth_password_reset_tokens")

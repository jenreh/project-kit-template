"""Create the first administrator from secrets.

The template ships no default credentials. This command runs safely any number of
times: it does nothing while an active administrator exists. The password has to be
changed at first login. Run it with `task admin:bootstrap`.
"""

import asyncio
import logging
import sys

from appkit_commons.configuration.logging import init_logging
from appkit_commons.configuration.secret_provider import (
    SecretNotFoundError,
    get_secret,
)
from appkit_commons.database.session import get_asyncdb_session
from appkit_user.authentication.backend.database.entities import UserEntity
from appkit_user.authentication.password_policy import PASSWORD_REGEX
from sqlalchemy import select

from app import configuration

logger = logging.getLogger(__name__)


class BootstrapError(ValueError):
    pass


def build_admin(email: str, password: str) -> UserEntity:
    """Validate the secrets and build the administrator entity."""
    if "@" not in email:
        raise BootstrapError("mn-admin-email must be an email address")
    if not PASSWORD_REGEX.match(password):
        raise BootstrapError(
            "mn-admin-password must have at least 12 characters with upper case, "
            "lower case, a digit and a special character"
        )
    admin = UserEntity(
        email=email,
        name="Administrator",
        is_active=True,
        is_admin=True,
        is_verified=True,
        needs_password_reset=True,
        roles=[],
    )
    admin.password = password
    return admin


async def bootstrap_admin() -> bool:
    """Create the administrator if there is none. Returns whether one was created."""
    async with get_asyncdb_session() as session:
        result = await session.execute(
            select(UserEntity.id).where(UserEntity.is_admin, UserEntity.is_active)
        )
        if result.first() is not None:
            logger.info("An active administrator exists, nothing to do")
            return False

        try:
            email = get_secret("mn-admin-email")
            password = get_secret("mn-admin-password")
        except SecretNotFoundError:
            logger.warning(
                "No active administrator exists. Set mn-admin-email and "
                "mn-admin-password and run this command again"
            )
            return False

        session.add(build_admin(email, password))
        logger.info("Created the first administrator")
        return True


def main() -> None:
    init_logging(configuration)
    try:
        asyncio.run(bootstrap_admin())
    except BootstrapError as e:
        logger.error("Cannot create the administrator: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()

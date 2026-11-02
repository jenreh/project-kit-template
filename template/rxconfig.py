import logging
from urllib.parse import urlsplit

import reflex as rx
from appkit_commons.configuration.configuration import ReflexConfig
from appkit_commons.configuration.logging import init_logging
from appkit_commons.database.configuration import DatabaseConfig
from appkit_commons.registry import service_registry

from app import configuration

init_logging(configuration)
logger = logging.getLogger(__name__)

database: DatabaseConfig | None = service_registry().get(DatabaseConfig)
reflex: ReflexConfig | None = service_registry().get(ReflexConfig)

deploy_url = (reflex.deploy_url if reflex else None) or "http://localhost:8080"
deploy_parts = urlsplit(deploy_url)

config = rx.Config(
    app_name="app",
    deploy_url=deploy_url,
    api_url=(reflex.api_url if reflex else None) or "http://localhost:3030",
    frontend_port=reflex.frontend_port if reflex else 8080,
    backend_port=reflex.backend_port if reflex else 3030,
    frontend_path=reflex.frontend_path if reflex else "",
    trusted_proxy_hops=reflex.trusted_proxy_hops if reflex else 0,
    # Reflex defaults to "*" with credentials allowed, which lets any website call
    # the backend and open its websocket as the signed-in user.
    cors_allowed_origins=[f"{deploy_parts.scheme}://{deploy_parts.netloc}"],
    db_url=database.url,
    async_db_url=database.url,
    telemetry_enabled=False,
    show_built_with_reflex=False,
    plugins=[
        rx.plugins.TailwindV4Plugin(),
        rx.plugins.RadixThemesPlugin(),
    ],
    disable_plugins=[rx.plugins.SitemapPlugin],
)

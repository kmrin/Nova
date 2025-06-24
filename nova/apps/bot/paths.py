from enum import StrEnum

from .helpers import get_os_path


class Path(StrEnum):
    ASSETS = get_os_path("assets")
    CONFIG = get_os_path("config/nova.yml")
    EXTENSIONS = get_os_path("extensions")
    LOCALE = get_os_path("locale")
    LOG_LATEST = get_os_path("/var/lib/nova/logs/latest.log", from_root=True)
    LOG_HISTORY = get_os_path("/var/lib/nova/logs/history", from_root=True)
    LOG_TRACEBACKS = get_os_path("/var/lib/nova/logs/tracebacks", from_root=True)
    CACHE = get_os_path("/var/lib/nova/cache", from_root=True)
    TREE_HASH = get_os_path("/var/lib/nova/cache/tree_hash.txt", from_root=True)
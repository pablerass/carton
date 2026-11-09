"""Local cache of BoardGameGeek data, kept in a file between runs."""
import logging
import os
import pickle
from pathlib import Path

from cartucho import ReturnCache
from cartucho.backends import MemoryBackend


def default_cache_file() -> Path:
    """Return CARTON_CACHE_FILE, or a file in the user cache directory."""
    if cache_file := os.environ.get('CARTON_CACHE_FILE'):
        return Path(cache_file)
    cache_home = os.environ.get('XDG_CACHE_HOME') or Path.home() / '.cache'
    return Path(cache_home) / 'carton' / 'bgg.pickle'


def load_cache(path: str | Path) -> ReturnCache:
    """Load the cache saved in path, or create an empty one if missing or unreadable.

    The file is unpickled, so it must only be writable by trusted users.
    """
    logger = logging.getLogger('carton.cache.load_cache')

    path = Path(path)
    if not path.exists():
        logger.debug(f"No cache found in {path}, starting with an empty one")
        return ReturnCache(MemoryBackend())

    try:
        cache = ReturnCache(MemoryBackend.load(path))
    except Exception as error:  # noqa: BLE001 - unpickling can raise almost anything
        # A broken or incompatible cache must not prevent using BGG
        logger.warning(f"Unable to load cache from {path}, starting with an empty one: {error}")
        return ReturnCache(MemoryBackend())

    logger.debug(f"Loaded {len(cache)} cache entries from {path}")
    return cache


def save_cache(cache: ReturnCache, path: str | Path) -> None:
    """Save the cache to path, logging instead of raising on errors."""
    logger = logging.getLogger('carton.cache.save_cache')

    backend = cache.backend
    if not isinstance(backend, MemoryBackend):
        raise TypeError(f"Only MemoryBackend caches can be saved, not {type(backend).__name__}")

    path = Path(path)
    try:
        # Write to a temporary file first so a failure does not corrupt the existing cache
        tmp_path = path.with_name(f'{path.name}.tmp')
        backend.save(tmp_path)
        tmp_path.replace(path)
    except (OSError, pickle.PicklingError) as error:
        logger.warning(f"Unable to save cache to {path}: {error}")
        return

    logger.debug(f"Saved {len(cache)} cache entries to {path}")

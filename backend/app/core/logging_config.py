import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.core.config import Settings

BACKEND_DIR = Path(__file__).resolve().parents[2]
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
LOG_DATE_SUFFIX = "%Y-%m-%d"

_FILE_HANDLER: TimedRotatingFileHandler | None = None
_CONSOLE_HANDLER: logging.StreamHandler | None = None
_CONFIGURED_LOGGERS: set[str] = set()


def _resolve_log_dir(settings: Settings) -> Path:
    log_dir = Path(settings.log_dir)
    if not log_dir.is_absolute():
        log_dir = BACKEND_DIR / log_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def _active_log_path(settings: Settings) -> Path:
    return _resolve_log_dir(settings) / settings.log_file


def _rotated_log_name(default_name: str) -> str:
    """Turn polyglot.log.2026-05-19 into polyglot-2026-05-19.log."""
    path = Path(default_name)
    marker = ".log."
    if marker not in path.name:
        return default_name
    stem, date_part = path.name.split(marker, 1)
    return str(path.parent / f"{stem}-{date_part}.log")


def _get_file_handler(settings: Settings, log_path: Path) -> TimedRotatingFileHandler:
    global _FILE_HANDLER
    if _FILE_HANDLER is not None:
        return _FILE_HANDLER

    formatter = logging.Formatter(LOG_FORMAT)
    _FILE_HANDLER = TimedRotatingFileHandler(
        log_path,
        when="midnight",
        interval=1,
        backupCount=settings.log_backup_days,
        encoding="utf-8",
        utc=False,
    )
    _FILE_HANDLER.suffix = LOG_DATE_SUFFIX
    _FILE_HANDLER.namer = _rotated_log_name
    _FILE_HANDLER.setFormatter(formatter)
    return _FILE_HANDLER


def _get_console_handler() -> logging.StreamHandler:
    global _CONSOLE_HANDLER
    if _CONSOLE_HANDLER is not None:
        return _CONSOLE_HANDLER

    formatter = logging.Formatter(LOG_FORMAT)
    _CONSOLE_HANDLER = logging.StreamHandler(sys.stderr)
    _CONSOLE_HANDLER.setFormatter(formatter)
    return _CONSOLE_HANDLER


def _ensure_logger(
    name: str | None,
    settings: Settings,
    handlers: list[logging.Handler],
) -> None:
    key = name or "root"
    if key in _CONFIGURED_LOGGERS:
        return

    logger = logging.getLogger(name)
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(level)
    for handler in handlers:
        if handler not in logger.handlers:
            logger.addHandler(handler)

    _CONFIGURED_LOGGERS.add(key)


def configure_logging(settings: Settings) -> Path:
    """
    Send application logs to stderr and a daily log file.

    The active file is backend/logs/polyglot.log. At midnight it is archived as
    polyglot-YYYY-MM-DD.log and a fresh polyglot.log is opened for the new day.
    """
    log_path = _active_log_path(settings)
    file_handler = _get_file_handler(settings, log_path)
    console_handler = _get_console_handler()

    _ensure_logger(None, settings, [file_handler, console_handler])

    # Uvicorn already logs to the console; attach only the file handler here.
    for logger_name in ("uvicorn.error", "uvicorn.access"):
        _ensure_logger(logger_name, settings, [file_handler])

    if "polyglot.logging" not in _CONFIGURED_LOGGERS:
        log_dir = log_path.parent.resolve()
        logging.getLogger("polyglot.logging").info(
            "Logging to stderr and %s (daily archives: %s/polyglot-YYYY-MM-DD.log)",
            log_path.resolve(),
            log_dir,
        )
        _CONFIGURED_LOGGERS.add("polyglot.logging")

    return log_path.resolve()

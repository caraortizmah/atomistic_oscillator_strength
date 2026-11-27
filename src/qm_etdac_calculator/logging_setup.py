"""
Logging setup for the qm_etdac_calculator program.

Library modules only emit messages:

    logger = logging.getLogger(__name__)
    logger.debug("...")

Only the program entry point (the CLI) calls configure_logging() to decide levels and
destinations. Without it, Python still prints WARNING and above to stderr, so warnings
are never lost (no NullHandler on purpose; decision D19 in docs/project-state.md).

Security (ADR 0005, CWE-117 log injection):
- untrusted(value) shows an untrusted value with repr(), truncated, inside a message.
- SafeFormatter escapes control characters (newline, carriage return, ANSI escape codes)
  in every message, so one record is always one line and cannot recolour a terminal.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

PACKAGE_LOGGER = "qm_etdac_calculator"  # parent of every module logger in the package
CONSOLE_FORMAT = "%(levelname)s: %(message)s"
FILE_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
FILE_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"  # ISO 8601 with UTC offset

# C0 and C1 control characters (includes \n, \r, \t and ESC, which starts ANSI codes)
_CONTROL_CHARACTERS = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_OWN_HANDLER = "_qm_etdac_handler"  # marks handlers created here, so others are never removed


def untrusted(value: object, limit: int = 80) -> str:
    """
    Show an untrusted value safely inside a message: repr() (quotes, escapes such as
    \\n and \\x1b become visible text), truncated to `limit` characters plus the full length.
    """
    text = repr(value)
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... ({len(text)} chars)"


def _escape_control_characters(text: str) -> str:
    return _CONTROL_CHARACTERS.sub(lambda match: f"\\x{ord(match.group()):02x}", text)


class SafeFormatter(logging.Formatter):
    """
    Formatter that escapes control characters in the message part of every record.

    Tracebacks (shown with --debug) are appended after this step by logging.Formatter,
    so they stay readable on several lines; they are produced by the program itself.
    """

    def formatMessage(self, record: logging.LogRecord) -> str:  # noqa: N802 (logging API name)
        return _escape_control_characters(super().formatMessage(record))


def configure_logging(
    verbose: bool = False,
    debug: bool = False,
    log_file: Path | None = None,
) -> logging.Logger:
    """
    Configure the package logger for a program run. Safe to call more than once.

    Args:
        verbose: show DEBUG messages on the console (default: INFO and above).
        debug: same console level as verbose; the CLI also shows full tracebacks (step 6).
        log_file: if given, also write every message (DEBUG and above) to this file, with
            time, level and module. The file must not exist yet: it is opened in mode "x"
            and never overwritten (ADR 0003); choosing a free name is the caller's job.
    Returns:
        The package logger.
    """
    logger = logging.getLogger(PACKAGE_LOGGER)
    for handler in list(logger.handlers):
        if getattr(handler, _OWN_HANDLER, False):  # remove only what an earlier call added
            logger.removeHandler(handler)
            handler.close()
    logger.setLevel(logging.DEBUG)  # every record is created; each handler filters by its level
    logger.propagate = False  # the program's own handlers only, no duplicates via the root logger

    console = logging.StreamHandler()  # stderr: results and messages never mix with stdout
    console.setLevel(logging.DEBUG if (verbose or debug) else logging.INFO)
    console.setFormatter(SafeFormatter(CONSOLE_FORMAT))
    setattr(console, _OWN_HANDLER, True)
    logger.addHandler(console)

    if log_file is not None:
        file_handler = logging.FileHandler(log_file, mode="x", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(SafeFormatter(FILE_FORMAT, datefmt=FILE_DATE_FORMAT))
        setattr(file_handler, _OWN_HANDLER, True)
        logger.addHandler(file_handler)

    return logger

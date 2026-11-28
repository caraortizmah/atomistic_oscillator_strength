"""Logging foundation: levels, log file, idempotent setup, and log-injection safety (ADR 0005)."""

from __future__ import annotations

import logging
from collections.abc import Iterator
from pathlib import Path

import pytest

from qm_etdac_calculator.logging_setup import (
    PACKAGE_LOGGER,
    PATH_LIMIT,
    SafeFormatter,
    configure_logging,
    untrusted,
    untrusted_path,
)

CHILD = f"{PACKAGE_LOGGER}.some_module"  # any module logger inside the package


@pytest.fixture(autouse=True)
def _reset_package_logger() -> Iterator[None]:
    """Leave the package logger as Python creates it, so tests do not affect each other."""
    yield
    logger = logging.getLogger(PACKAGE_LOGGER)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    logger.setLevel(logging.NOTSET)
    logger.propagate = True


# --- untrusted(): ADR 0005 message safety -------------------------------------------


# --- untrusted_path(): complete paths, still escaped (decision of step 6.3) -----------


def test_path_limit_is_the_linux_path_maximum() -> None:
    assert PATH_LIMIT == 4096


def test_untrusted_path_shows_a_long_path_whole() -> None:
    path = Path("/cluster/project") / ("a" * 200) / "etdac_outputs" / "data_etdac_matrix.h5"
    assert untrusted_path(path) == repr(str(path))


@pytest.mark.parametrize(("length", "whole"), [(PATH_LIMIT - 2, True), (PATH_LIMIT - 1, False)])
def test_untrusted_path_boundary(length: int, whole: bool) -> None:
    """repr() adds two quotes: a path of PATH_LIMIT - 2 characters is shown whole, one more is cut."""
    path = "/" + "a" * (length - 1)
    assert (untrusted_path(path) == repr(path)) is whole


def test_untrusted_path_still_escapes_control_characters() -> None:
    assert untrusted_path("/data/a\nINFO: forged\x1b[31m") == "'/data/a\\nINFO: forged\\x1b[31m'"


def test_untrusted_shows_the_value_with_repr() -> None:
    assert untrusted("f10") == "'f10'"
    assert untrusted("f10\nINFO: forged") == "'f10\\nINFO: forged'"  # newline visible, not executed


def test_untrusted_escapes_terminal_codes() -> None:
    assert "\x1b" not in untrusted("\x1b[31mred")


def test_untrusted_truncates_long_values() -> None:
    text = untrusted("A" * 10_000, limit=80)
    assert len(text) < 120
    assert text.endswith("(10002 chars)")  # length of the full repr, quotes included


def test_untrusted_keeps_short_values_whole() -> None:
    assert untrusted("x" * 10, limit=80) == "'" + "x" * 10 + "'"


# --- SafeFormatter: CWE-117 log injection ------------------------------------------


def _record(message: str, exc_info: object = None) -> logging.LogRecord:
    return logging.LogRecord(CHILD, logging.INFO, __file__, 1, message, None, exc_info)  # type: ignore[arg-type]


def test_safe_formatter_keeps_one_record_on_one_line() -> None:
    line = SafeFormatter("%(levelname)s: %(message)s").format(_record("f10\nINFO: forged line"))
    assert "\n" not in line
    assert line == "INFO: f10\\x0aINFO: forged line"


def test_safe_formatter_escapes_terminal_codes() -> None:
    line = SafeFormatter("%(message)s").format(_record("\x1b[31mred\x1b[0m"))
    assert "\x1b" not in line
    assert line == "\\x1b[31mred\\x1b[0m"


def test_safe_formatter_leaves_plain_text_unchanged() -> None:
    assert SafeFormatter("%(message)s").format(_record("ETDAC calculated for 52 samples")) == (
        "ETDAC calculated for 52 samples"
    )


def test_safe_formatter_keeps_tracebacks_readable() -> None:
    """--debug shows full tracebacks: only the message is escaped, the traceback stays multi-line."""
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        line = SafeFormatter("%(message)s").format(_record("failed", sys.exc_info()))
    first, rest = line.split("\n", 1)
    assert first == "failed"
    assert rest.startswith("Traceback (most recent call last):")


# --- configure_logging(): levels, file, idempotence ---------------------------------


def test_console_shows_info_but_not_debug_by_default(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging()
    logging.getLogger(CHILD).debug("hidden detail")
    logging.getLogger(CHILD).info("progress message")
    err = capsys.readouterr().err
    assert "INFO: progress message" in err
    assert "hidden detail" not in err


@pytest.mark.parametrize("flags", [{"verbose": True}, {"debug": True}])
def test_verbose_and_debug_show_debug_messages(flags: dict[str, bool], capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging(**flags)
    logging.getLogger(CHILD).debug("detail")
    assert "DEBUG: detail" in capsys.readouterr().err


def test_log_file_receives_debug_with_time_and_module(tmp_path: Path) -> None:
    log_file = tmp_path / "etdac_run.log"
    configure_logging(log_file=log_file)
    logging.getLogger(CHILD).debug("detail for the record")
    for handler in logging.getLogger(PACKAGE_LOGGER).handlers:
        handler.flush()
    line = log_file.read_text(encoding="utf-8").strip()
    assert line.endswith(f"DEBUG    {CHILD}: detail for the record")
    assert line[:4].isdigit()  # starts with the date (ISO 8601)


def test_log_file_is_never_overwritten(tmp_path: Path) -> None:
    """ADR 0003: an existing file is never replaced; choosing a free name is the caller's job (5e)."""
    log_file = tmp_path / "etdac_run.log"
    log_file.write_text("earlier run\n", encoding="utf-8")
    with pytest.raises(FileExistsError):
        configure_logging(log_file=log_file)
    assert log_file.read_text(encoding="utf-8") == "earlier run\n"


def test_configuring_twice_does_not_duplicate_messages(capsys: pytest.CaptureFixture[str]) -> None:
    configure_logging()
    configure_logging(verbose=True)
    logging.getLogger(CHILD).info("once")
    assert capsys.readouterr().err.count("once") == 1


def test_handlers_added_by_others_are_left_alone() -> None:
    foreign = logging.NullHandler()
    logging.getLogger(PACKAGE_LOGGER).addHandler(foreign)
    configure_logging()
    configure_logging()
    assert foreign in logging.getLogger(PACKAGE_LOGGER).handlers

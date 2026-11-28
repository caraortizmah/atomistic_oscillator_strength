"""The `qm-etdac` command (step 6.3: `noauto`).

The tests call cli.main(argv) in the same process, on a copy of the Phe-Tyr folder, so
nothing is written into tests/data/. Console messages go to stderr (captured with capsys).
"""

from __future__ import annotations

import logging
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import REFERENCE_H5, assert_etdac_equal, read_etdac_h5

from qm_etdac_calculator.cli import main
from qm_etdac_calculator.logging_setup import PACKAGE_LOGGER

LIST_INPUT = ["--list-input", "resA_MOcore_list.log", "resB_MOvirt_list.log", "corevirt_fosce_AB_list.log"]


@pytest.fixture(autouse=True)
def _reset_package_logger() -> Iterator[None]:
    """main() configures logging (console and run log); close it so tests do not affect each other."""
    yield
    logger = logging.getLogger(PACKAGE_LOGGER)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()
    logger.setLevel(logging.NOTSET)
    logger.propagate = True


@pytest.fixture
def project(phe_tyr_dir: Path, tmp_path: Path) -> Path:
    copy = tmp_path / "phe_tyr"
    shutil.copytree(phe_tyr_dir, copy, ignore=shutil.ignore_patterns("reference"))
    return copy


def test_help_lists_noauto(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])
    assert exit_info.value.code == 0
    assert "noauto" in capsys.readouterr().out


@pytest.mark.golden
def test_noauto_writes_the_reference_result_and_the_run_log(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["noauto", *LIST_INPUT, "--paths-inout", str(project)]) == 0
    output = project / "etdac_outputs"
    assert_etdac_equal(read_etdac_h5(output / "data_etdac_matrix.h5"), read_etdac_h5(REFERENCE_H5))
    log = (output / "data_etdac_matrix.log").read_text(encoding="utf-8")
    assert "wrote 52 sample(s)" in log
    assert "data_etdac_matrix.h5" in capsys.readouterr().err  # the result is named on the console


def test_noauto_uses_the_current_folder_when_no_folder_is_given(project: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(project)
    assert main(["noauto", *LIST_INPUT]) == 0
    assert (project / "etdac_outputs" / "data_etdac_matrix.h5").is_file()


def test_an_input_error_is_one_line_without_traceback(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    argv = ["noauto", "--list-input", "missing.log", "resB_MOvirt_list.log", "corevirt_fosce_AB_list.log"]
    assert main([*argv, "--paths-inout", str(project)]) == 1
    err = capsys.readouterr().err
    assert "ERROR: list file not found" in err
    assert "Traceback" not in err
    assert not (project / "etdac_outputs" / "data_etdac_matrix.h5").exists()


def test_debug_adds_the_traceback(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    argv = ["noauto", "--list-input", "missing.log", "resB_MOvirt_list.log", "corevirt_fosce_AB_list.log"]
    assert main([*argv, "--paths-inout", str(project), "--debug"]) == 1
    assert "Traceback" in capsys.readouterr().err


def test_list_input_is_required(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["noauto"])
    assert exit_info.value.code == 2
    assert "--list-input" in capsys.readouterr().err


def test_an_output_folder_is_rejected_with_an_explanation(project: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Until step 6.2 the second value of --paths-inout was the output folder (ADR 0007)."""
    with pytest.raises(SystemExit) as exit_info:
        main(["noauto", *LIST_INPUT, "--paths-inout", str(project), str(project / "out")])
    assert exit_info.value.code == 2
    assert "results go to LOGS/etdac_outputs" in capsys.readouterr().err
    assert not (project / "out").exists()

"""Run settings (step 5f-1): ConfigMan holds the five documented settings of a run.

The keys are those of `qm-etdac auto` JSON files and of the old manager script, so
ConfigMan(**settings) keeps working. ConfigMan checks no files: Controler does that, with
the path policy (ADR 0003). Reading a JSON file is step 6.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from qm_etdac_calculator import ConfigMan, Controler, default_data_root
from qm_etdac_calculator.outputs import DEFAULT_OUTPUT_DIR

SETTINGS = {
    "corepop": "resA_MOcore_list.log",
    "virtpop": "resB_MOvirt_list.log",
    "etranscv": "corevirt_fosce_AB_list.log",
    "logspath": "tests/data/phe_tyr",
    "outputpath": "results",
}


def test_documented_keys_build_the_settings() -> None:
    config = ConfigMan(**SETTINGS)
    assert dataclasses.asdict(config) == SETTINGS


def test_output_folder_defaults_to_etdac_outputs() -> None:
    settings = {key: value for key, value in SETTINGS.items() if key != "outputpath"}
    assert ConfigMan(**settings).outputpath == DEFAULT_OUTPUT_DIR == "etdac_outputs"


@pytest.mark.parametrize("missing", ["corepop", "virtpop", "etranscv", "logspath"])
def test_a_missing_required_setting_is_rejected(missing: str) -> None:
    settings = {key: value for key, value in SETTINGS.items() if key != missing}
    with pytest.raises(TypeError, match=missing):
        ConfigMan(**settings)


def test_an_unknown_setting_is_rejected() -> None:
    with pytest.raises(TypeError, match="corepopp"):
        ConfigMan(**SETTINGS, corepopp="typo.log")


def test_settings_cannot_change_during_a_run() -> None:
    config = ConfigMan(**SETTINGS)
    with pytest.raises(dataclasses.FrozenInstanceError):
        config.corepop = "other.log"  # type: ignore[misc]


def test_list_files_are_in_the_logs_folder_in_input_order() -> None:
    files = ConfigMan(**SETTINGS).list_files()
    logs = Path("tests/data/phe_tyr")
    assert files == (
        logs / "resA_MOcore_list.log",
        logs / "resB_MOvirt_list.log",
        logs / "corevirt_fosce_AB_list.log",
    )
    assert (files.core, files.virt, files.etrans) == tuple(files)


def test_list_files_are_readable_by_the_controler(phe_tyr_dir: Path) -> None:
    config = ConfigMan(**{**SETTINGS, "logspath": str(phe_tyr_dir)})
    reader = Controler(default_data_root(config.logspath))
    assert [len(reader.read_list_file(path)) for path in config.list_files()] == [52, 52, 52]

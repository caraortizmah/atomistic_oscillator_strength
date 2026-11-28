"""Run settings (step 5f-1): ConfigMan holds the five documented settings of a run.

The keys are those of `qm-etdac auto` JSON files and of the old manager script, so
ConfigMan(**settings) keeps working. ConfigMan checks no files: Controler does that, with
the path policy (ADR 0003). Reading a JSON file is step 6. Since step 6.2 the output folder
is not a setting: it is always `etdac_outputs` inside the logs folder (ADR 0007).
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from qm_etdac_calculator import ConfigMan, Controler, InputError, default_data_root
from qm_etdac_calculator.config import read_config
from qm_etdac_calculator.outputs import DEFAULT_OUTPUT_DIR

SETTINGS = {
    "corepop": "resA_MOcore_list.log",
    "virtpop": "resB_MOvirt_list.log",
    "etranscv": "corevirt_fosce_AB_list.log",
    "logspath": "tests/data/phe_tyr",
}


def test_documented_keys_build_the_settings() -> None:
    config = ConfigMan(**SETTINGS)
    assert dataclasses.asdict(config) == SETTINGS


def test_output_folder_is_etdac_outputs_inside_the_logs_folder() -> None:
    assert ConfigMan(**SETTINGS).output_dir() == Path("tests/data/phe_tyr") / "etdac_outputs"
    assert DEFAULT_OUTPUT_DIR == "etdac_outputs"


@pytest.mark.parametrize("missing", ["corepop", "virtpop", "etranscv", "logspath"])
def test_a_missing_required_setting_is_rejected(missing: str) -> None:
    settings = {key: value for key, value in SETTINGS.items() if key != missing}
    with pytest.raises(TypeError, match=missing):
        ConfigMan(**settings)


@pytest.mark.parametrize("unknown", ["corepopp", "outputpath"])
def test_an_unknown_setting_is_rejected(unknown: str) -> None:
    """outputpath was a setting until step 6.2; the output folder is no longer chosen (ADR 0007)."""
    with pytest.raises(TypeError, match=unknown):
        ConfigMan(**SETTINGS, **{unknown: "somewhere"})


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


# --- read_config(): the JSON file of `qm-etdac auto` (step 6.4, strict schema, ADR 0003) --


def _config_file(tmp_path: Path, content: str | bytes) -> Path:
    path = tmp_path / "run.json"
    path.write_bytes(content.encode("utf-8") if isinstance(content, str) else content)
    return path


def test_read_config_builds_the_settings(tmp_path: Path) -> None:
    assert read_config(_config_file(tmp_path, json.dumps(SETTINGS))) == ConfigMan(**SETTINGS)


def test_a_missing_config_file_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(InputError, match="config file not found"):
        read_config(tmp_path / "missing.json")


def test_a_config_file_that_is_not_utf8_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(InputError, match="not valid UTF-8"):
        read_config(_config_file(tmp_path, b'{"corepop": "\xff"}'))


def test_invalid_json_names_line_and_column(tmp_path: Path) -> None:
    with pytest.raises(InputError, match="not valid JSON.*line 2, column 1"):
        read_config(_config_file(tmp_path, '{"corepop": "a",\n'))


def test_the_config_must_be_a_json_object(tmp_path: Path) -> None:
    with pytest.raises(InputError, match="must be a JSON object"):
        read_config(_config_file(tmp_path, json.dumps(list(SETTINGS))))


def test_unknown_keys_are_listed(tmp_path: Path) -> None:
    with pytest.raises(InputError, match="unknown key 'corepopp'"):
        read_config(_config_file(tmp_path, json.dumps({**SETTINGS, "corepopp": "typo.log"})))


def test_outputpath_is_explained(tmp_path: Path) -> None:
    """outputpath was a setting until step 6.2 (ADR 0007); old files get an explanation, not only 'unknown key'."""
    with pytest.raises(InputError, match="'outputpath' is no longer a setting: results go to <logspath>/etdac_outputs"):
        read_config(_config_file(tmp_path, json.dumps({**SETTINGS, "outputpath": "results"})))


def test_missing_keys_are_listed(tmp_path: Path) -> None:
    settings = {key: value for key, value in SETTINGS.items() if key not in ("virtpop", "logspath")}
    with pytest.raises(InputError, match="missing keys 'logspath', 'virtpop'"):
        read_config(_config_file(tmp_path, json.dumps(settings)))


@pytest.mark.parametrize("value", [1, None, ["a.log"], ""])
def test_values_must_be_non_empty_strings(tmp_path: Path, value: object) -> None:
    with pytest.raises(InputError, match="'corepop' must be a non-empty string"):
        read_config(_config_file(tmp_path, json.dumps({**SETTINGS, "corepop": value})))


def test_a_duplicate_key_is_rejected(tmp_path: Path) -> None:
    """Python's json keeps the last of two equal keys silently; the run would use a value nobody chose."""
    text = json.dumps(SETTINGS)[:-1] + ', "logspath": "other"}'
    with pytest.raises(InputError, match="duplicate key 'logspath'"):
        read_config(_config_file(tmp_path, text))

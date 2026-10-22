from __future__ import annotations

import pytest

from calc.__main__ import main


def test_cli_summary(capsys: pytest.CaptureFixture[str]) -> None:
    args = ["--price", "300000", "--down", "60000", "--rate", "4.5", "--years", "30"]
    assert main(args + ["--tax", "1200", "--insurance", "600", "--first", "2026-11"]) == 0
    out = capsys.readouterr().out
    assert "1366.04" in out
    assert "2056-10" in out


def test_cli_invalid_input(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--price", "100", "--down", "200", "--rate", "4", "--years", "30"]) == 2
    assert "Akontácia" in capsys.readouterr().err

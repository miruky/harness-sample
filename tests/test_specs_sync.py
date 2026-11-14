from __future__ import annotations

from pathlib import Path

import pytest

from tools import specs_sync


@pytest.fixture
def spec(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    specs = tmp_path / "docs" / "specs"
    specs.mkdir(parents=True)
    path = specs / "0001-export.md"
    path.write_text("# 予約のCSV出力\n\n- 列は id、room の順\n", encoding="utf-8")
    monkeypatch.setattr(specs_sync, "ROOT", tmp_path)
    monkeypatch.setattr(specs_sync, "SPECS", specs)
    monkeypatch.setattr(specs_sync, "LEDGER", specs / ".sync.json")
    return path


def test_unrecorded_spec_is_stale(spec: Path) -> None:
    assert specs_sync.status() == 1


def test_recorded_spec_is_not_stale_until_it_changes(spec: Path) -> None:
    specs_sync.record(spec, "101", 1)
    assert specs_sync.status() == 0
    spec.write_text(spec.read_text(encoding="utf-8") + "- 並びは開始の早い順\n", encoding="utf-8")
    assert specs_sync.status() == 1


def test_same_version_needs_no_body(spec: Path, capsys: pytest.CaptureFixture[str]) -> None:
    specs_sync.record(spec, "101", 3)
    capsys.readouterr()
    assert specs_sync.check(spec, 3) == 0
    assert "本文の取得は不要" in capsys.readouterr().out


def test_newer_version_asks_for_diff_only(spec: Path, capsys: pytest.CaptureFixture[str]) -> None:
    specs_sync.record(spec, "101", 3)
    capsys.readouterr()
    assert specs_sync.check(spec, 4) == 1
    assert "差分だけ" in capsys.readouterr().out


def test_payload_ends_with_hash_of_the_markdown(
    spec: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    specs_sync.payload(spec)
    out = capsys.readouterr().out
    assert f"sha256:{specs_sync.digest(spec.read_text(encoding='utf-8'))}" in out

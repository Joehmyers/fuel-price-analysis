from src import config
from src.fetch import fuel_finder


def test_collector_refuses_to_run_without_a_link(monkeypatch, capsys):
    monkeypatch.setattr(config, "FUEL_FINDER_CSV_URL", "")
    assert fuel_finder.main() == 1
    assert "FUEL_FINDER_CSV_URL" in capsys.readouterr().err


def test_collector_saves_snapshot_with_fetch_time(monkeypatch, tmp_path):
    class Fake:
        content = b"a,b\n1,2\n"

    monkeypatch.setattr(config, "FUEL_FINDER_CSV_URL", "https://example.test/x.csv")
    monkeypatch.setattr(config, "RAW_DIR", tmp_path)
    monkeypatch.setattr(fuel_finder.common, "get", lambda url: Fake())
    assert fuel_finder.main() == 0
    saved = list((tmp_path / "fuel_finder").glob("*__fuel_finder.csv"))
    assert len(saved) == 1 and saved[0].read_bytes() == Fake.content

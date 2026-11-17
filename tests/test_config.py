from src import config


def test_data_folders_sit_under_one_data_dir():
    assert config.RAW_DIR.parent == config.DATA_DIR
    assert config.CLEAN_DIR.parent == config.DATA_DIR


def test_no_credential_default_in_config():
    # The official CSV link comes from the environment, never from code.
    assert config.FUEL_FINDER_CSV_URL == "" or config.FUEL_FINDER_CSV_URL.startswith("http")

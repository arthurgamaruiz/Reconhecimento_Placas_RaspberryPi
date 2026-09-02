from catraca.config import Config


def test_defaults():
    cfg = Config.from_env(env={})
    assert cfg.camera_index == 0
    assert cfg.ocr_conf_threshold == 0.85
    assert cfg.fallback_enabled is False
    assert cfg.cloud_url == ""


def test_env_override_and_cast():
    cfg = Config.from_env(env={
        "CATRACA_CAMERA_INDEX": "2",
        "CATRACA_OCR_CONF_THRESHOLD": "0.9",
        "CATRACA_FALLBACK_ENABLED": "true",
        "CATRACA_CLOUD_URL": "https://x.example",
    })
    assert cfg.camera_index == 2
    assert cfg.ocr_conf_threshold == 0.9
    assert cfg.fallback_enabled is True
    assert cfg.cloud_url == "https://x.example"


def test_bool_falsy_values():
    assert Config.from_env(env={"CATRACA_FALLBACK_ENABLED": "0"}).fallback_enabled is False
    assert Config.from_env(env={"CATRACA_FALLBACK_ENABLED": "yes"}).fallback_enabled is True

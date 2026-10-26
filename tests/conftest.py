"""Shared fixtures. Tests must never see the developer's real config or credentials."""
import pytest


@pytest.fixture(autouse=True)
def _isolated_user_config(tmp_path_factory, monkeypatch):
    from syzetetes import config as conf
    home = tmp_path_factory.mktemp("xdg") / "syzetetes"
    monkeypatch.setattr(conf, "CONFIG_DIR", home)
    monkeypatch.setattr(conf, "USER_CONFIG", home / "config.toml")
    monkeypatch.setattr(conf, "CREDENTIALS", home / "credentials.toml")
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)

from app.utils import env


def _use_env_file(monkeypatch, env_file):
    monkeypatch.setattr(env, "ENV_FILE", env_file)


def test_get_settings_loads_env_file_before_reading_values(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("GROQ_API_KEY=env-file-key\n", encoding="utf-8")
    _use_env_file(monkeypatch, env_file)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    env.load_environment()

    settings = env.get_settings()

    assert settings.groq_api_key == "env-file-key"


def test_env_file_key_replaces_blank_inherited_groq_key(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("GROQ_API_KEY=env-file-key\n", encoding="utf-8")
    _use_env_file(monkeypatch, env_file)
    monkeypatch.setenv("GROQ_API_KEY", "")
    env.load_environment()

    settings = env.get_settings()

    assert settings.groq_api_key == "env-file-key"


def test_missing_env_file_leaves_groq_key_unset(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    _use_env_file(monkeypatch, env_file)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    env.load_environment()

    settings = env.get_settings()

    assert settings.groq_api_key is None


def test_initialize_settings_loads_env_file_before_building_settings(
    tmp_path, monkeypatch
):
    env_file = tmp_path / ".env"
    env_file.write_text("GROQ_API_KEY=env-file-key\n", encoding="utf-8")
    _use_env_file(monkeypatch, env_file)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    settings = env.initialize_settings()

    assert settings.groq_api_key == "env-file-key"


def test_create_app_initializes_settings_from_env_file(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("GROQ_API_KEY=env-file-key\n", encoding="utf-8")
    _use_env_file(monkeypatch, env_file)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    from main import create_app

    app = create_app()

    assert app.state.settings.groq_api_key == "env-file-key"

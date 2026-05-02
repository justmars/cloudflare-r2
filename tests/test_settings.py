from pydantic import ValidationError

from src.r2.settings import R2Settings


def test_required_settings_validation(monkeypatch):
    for name in (
        "R2_ACCOUNT_ID",
        "CF_ACCT_ID",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    try:
        R2Settings(_env_file=None)
    except ValidationError as exc:
        fields = {error["loc"][0] for error in exc.errors()}
        assert {"R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY"} <= fields
    else:
        raise AssertionError("R2Settings should reject missing required settings")


def test_dotenv_loading(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "R2_ACCOUNT_ID=acct",
                "R2_BUCKET=bucket",
                "R2_ACCESS_KEY_ID=key",
                "R2_SECRET_ACCESS_KEY=secret",
            ]
        )
    )

    settings = R2Settings(_env_file=env_file)

    assert settings.account_id == "acct"
    assert settings.bucket_name == "bucket"
    assert settings.bucket == "bucket"
    assert settings.endpoint_url == "https://acct.r2.cloudflarestorage.com"
    assert settings.region == "auto"


def test_legacy_aliases_and_endpoint_override(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "CF_ACCT_ID=legacy",
                "CF_R2_REGION=wnam",
                "R2_ACCESS_KEY_ID=key",
                "R2_SECRET_ACCESS_KEY=secret",
                "R2_ENDPOINT_URL=https://example.invalid/custom/",
            ]
        )
    )

    settings = R2Settings(_env_file=env_file)

    assert settings.account_id == "legacy"
    assert settings.region == "wnam"
    assert settings.endpoint_url == "https://example.invalid/custom"


def test_secret_redaction():
    settings = R2Settings(
        account_id="acct",
        access_key_id="abcd1234",
        secret_access_key="secret",
    )

    redacted = settings.redacted_dict()

    assert redacted["access_key_id"] == "abcd..."
    assert redacted["secret_access_key"] == "**********"
    assert "SecretStr('**********')" in repr(settings)
    assert "abcd1234" not in repr(settings)

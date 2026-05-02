from click.testing import CliRunner

from src.r2.__main__ import cli
from src.r2.transfer import TransferSummary


def test_doctor_validates_settings_and_bucket_access(monkeypatch):
    monkeypatch.setenv("R2_ACCOUNT_ID", "acct")
    monkeypatch.setenv("R2_BUCKET", "bucket")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "secret")
    called = {}

    def fake_verify_bucket(*, settings, client=None):
        called["bucket"] = settings.bucket_name
        return True

    monkeypatch.setattr("src.r2.__main__.verify_bucket", fake_verify_bucket)

    result = CliRunner().invoke(cli, ["doctor", "--show-bucket"])

    assert result.exit_code == 0
    assert called["bucket"] == "bucket"
    assert "bucket=bucket" in result.output


def test_upload_dir_passes_options(monkeypatch, tmp_path):
    monkeypatch.setenv("R2_ACCOUNT_ID", "acct")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "secret")
    captured = {}

    def fake_upload_directory(source, **kwargs):
        captured["source"] = source
        captured.update(kwargs)
        return TransferSummary(bucket="bucket", prefix="pref/", records=[])

    monkeypatch.setattr("src.r2.__main__.upload_directory", fake_upload_directory)

    result = CliRunner().invoke(
        cli,
        [
            "upload-dir",
            "--source",
            str(tmp_path),
            "--bucket",
            "bucket",
            "--prefix",
            "pref",
            "--overwrite",
            "replace",
            "--dry-run",
        ],
    )

    assert result.exit_code == 0
    assert captured["source"] == str(tmp_path)
    assert captured["bucket"] == "bucket"
    assert captured["prefix"] == "pref"
    assert captured["overwrite"] == "replace"
    assert captured["dry_run"] is True


def test_download_prefix_passes_options(monkeypatch, tmp_path):
    monkeypatch.setenv("R2_ACCOUNT_ID", "acct")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "secret")
    captured = {}

    def fake_download_prefix(target, **kwargs):
        captured["target"] = target
        captured.update(kwargs)
        return TransferSummary(bucket="bucket", prefix="pref/", records=[])

    monkeypatch.setattr("src.r2.__main__.download_prefix", fake_download_prefix)

    result = CliRunner().invoke(
        cli,
        [
            "download-prefix",
            "--target",
            str(tmp_path),
            "--bucket",
            "bucket",
            "--prefix",
            "pref",
            "--strip-prefix",
        ],
    )

    assert result.exit_code == 0
    assert captured["target"] == str(tmp_path)
    assert captured["bucket"] == "bucket"
    assert captured["prefix"] == "pref"
    assert captured["preserve_key"] is False


def test_existing_single_file_commands_remain_available():
    commands = cli.commands.keys()

    assert {"upload", "download", "upload-dir", "download-prefix", "doctor"} <= set(
        commands
    )

# Modernize Cloudflare R2 Package For Directory Sync

## Summary
Update this package as the reusable R2 layer for DepEd projects. Keep the existing package and CLI identity (`cloudflare-r2`, import package `r2`, command `r2`), raise the runtime requirement to Python `>=3.14`, and add directory upload/download workflows that replace the copied `bucket.py` logic in `deped-dataset-extend`.

The package should remain a thin, typed wrapper around Cloudflare R2’s S3-compatible boto3 API, with configuration loaded through environment variables or `.env` files, including 1Password-injected or 1Password-mounted dotenv files.

## Key Changes

- Update `pyproject.toml`:
  - Set `requires-python = ">=3.14"`.
  - Add `pydantic-settings` and `python-dotenv`.
  - Keep `boto3`, `rich`, and `click`.
  - Fix `testpaths` to match the actual package path: `tests`, `src/r2`.

- Replace hard-coded R2 settings in `src/r2/cf.py`:
  - Default region must be `auto`, matching current Cloudflare S3 SDK guidance.
  - Keep `CF_ACCT_ID` and `CF_R2_REGION` as backward-compatible aliases.
  - Add canonical env vars: `R2_ACCOUNT_ID`, `R2_BUCKET`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, optional `R2_ENDPOINT_URL`, `R2_REGION=auto`, and `R2_PREFIX`.
  - Do not use fake credential defaults like `"ABC"` / `"XYZ"` for required secrets.

- Add settings and transfer modules:
  - `src/r2/settings.py`: `R2Settings` using `pydantic-settings`, `SecretStr`, `.env` support, aliases, endpoint construction, and redacted display.
  - `src/r2/transfer.py`: directory sync functions and typed summary models.
  - `src/r2/exceptions.py`: package-specific errors for missing settings, bucket access failure, transfer failure, and invalid path mapping.

- Preserve existing single-object API where practical:
  - Keep `CloudflareR2` and `CloudflareR2Bucket` as compatibility wrappers.
  - Stop adding broad new `except Exception: return None` behavior.
  - New sync APIs should raise explicit errors and return summary objects.

## Public API And CLI

Expose these library functions from `src/r2/__init__.py`:

- `create_client(settings: R2Settings | None = None)`
- `verify_bucket(settings: R2Settings | None = None, client=None)`
- `upload_directory(source_dir, *, bucket=None, prefix=None, overwrite="skip", exclude=(".DS_Store",), dry_run=False, settings=None, client=None)`
- `download_prefix(target_dir, *, bucket=None, prefix=None, preserve_key=True, overwrite="replace", dry_run=False, settings=None, client=None)`

Add these CLI commands in `src/r2/__main__.py`:

- `r2 doctor --env-file .env --show-bucket`
- `r2 upload-dir --source data --prefix "" --overwrite skip`
- `r2 download-prefix --target data --prefix "" --preserve-key`
- Keep existing `r2 upload --bucket --src --key` and `r2 download --bucket --key` for single-file compatibility.

Overwrite modes:

- Upload: `skip`, `replace`, `fail`.
- Download: `replace`, `skip`, `fail`.
- `dry_run=True` returns the planned transfers without writing locally or remotely.

Path rules:

- Upload keys are `prefix + relative path from source_dir`, normalized to POSIX separators.
- Download preserves object keys under `target_dir` by default.
- Skip directory marker objects ending in `/`.
- Exclude `.DS_Store` by default.

## Documentation

Update `README.md`, `docs/index.md`, and `env.example` with:

- Install and quick-start examples.
- Full parameter table for settings and CLI flags.
- 1Password usage:
  - `op inject -i env.example -o .env`
  - `op run --env-file .env -- r2 doctor`
  - Mounted 1Password local `.env` files.
- Cloudflare R2 setup notes:
  - Account ID and endpoint format.
  - Bucket-scoped read/write token.
  - `R2_REGION=auto`.
- Migration example for `deped-dataset-extend`:
  - `just download` should delegate to `uv run r2 download-prefix --target data`.
  - `just upload` should delegate to `uv run r2 upload-dir --source data`.

## Test Plan

- Settings tests:
  - Required-field validation.
  - `.env` loading.
  - `R2_ACCOUNT_ID` and legacy `CF_ACCT_ID`.
  - `R2_REGION` and legacy `CF_R2_REGION`.
  - Secret redaction.
  - Endpoint override and default endpoint construction.

- Transfer tests with fake S3 client:
  - Directory upload discovers nested files.
  - `.DS_Store` is excluded.
  - Prefix joining is stable.
  - Upload overwrite modes call `head_object`, `delete_object`, and `upload_file` correctly.
  - Download prefix lists paginated objects.
  - Directory marker keys are skipped.
  - Download creates parent directories.
  - Dry runs make no write calls.

- CLI tests:
  - `r2 doctor` validates settings and bucket access.
  - `r2 upload-dir` and `r2 download-prefix` pass expected options to transfer functions.
  - Existing `r2 upload` and `r2 download` still work for single-file use.

- Verification commands:
  - `uv run pytest`
  - `uv run mkdocs build`
  - Optional live smoke test only when credentials are present: `RUN_R2_INTEGRATION=1 uv run pytest tests/test_integration_r2.py`

## Assumptions

- Work is executed from the root of this repo: `cloudflare-r2`.
- This repo is the reusable package home; do not create a second package.
- Python `>=3.14` is intentional even though older published versions supported Python `>=3.11`.
- 1Password remains outside the runtime dependency graph; the package consumes env vars or dotenv files only.
- Cloudflare R2 SDK configuration follows the current S3 docs: endpoint `https://<account_id>.r2.cloudflarestorage.com` and region `auto`.

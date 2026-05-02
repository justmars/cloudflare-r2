# Cloudflare R2

`cloudflare-r2` provides a small Python package and `r2` command for common
Cloudflare R2 workflows:

- validate dotenv-based R2 settings
- upload local directories into bucket prefixes
- download bucket prefixes into local directories
- keep older single-object upload/download commands available

Cloudflare R2 is S3-compatible. This package uses `boto3` under the hood and
builds the endpoint as `https://<account_id>.r2.cloudflarestorage.com` unless
you provide an override.

## Install

```sh
uv add cloudflare-r2
```

## Configure

Create a `.env` file next to the command you run:

```sh
R2_ACCOUNT_ID=your-account-id
R2_BUCKET=your-bucket
R2_ACCESS_KEY_ID=your-token-key
R2_SECRET_ACCESS_KEY=your-token-secret
R2_REGION=auto
R2_PREFIX=
```

Then check that credentials and bucket access are valid:

```sh
r2 doctor --env-file .env --show-bucket
```

### Settings

| Setting | Required | Default | Notes |
| --- | --- | --- | --- |
| `R2_ACCOUNT_ID` | Yes | | Cloudflare account ID. `CF_ACCT_ID` is accepted for compatibility. |
| `R2_BUCKET` | For bucket operations | | Default bucket for `doctor`, uploads, and downloads. |
| `R2_ACCESS_KEY_ID` | Yes | | Bucket-scoped R2 token access key. |
| `R2_SECRET_ACCESS_KEY` | Yes | | Bucket-scoped R2 token secret. |
| `R2_ENDPOINT_URL` | No | `https://<account_id>.r2.cloudflarestorage.com` | Optional endpoint override. |
| `R2_REGION` | No | `auto` | Cloudflare S3-compatible region. `CF_R2_REGION` is accepted. |
| `R2_PREFIX` | No | | Default object prefix. |

Create a bucket-scoped read/write R2 API token in the Cloudflare dashboard. Keep
`R2_REGION=auto` unless Cloudflare changes its S3 SDK guidance.

## Command Line

### Validate Access

```sh
r2 doctor --env-file .env --show-bucket
```

`doctor` loads settings, checks bucket access with `head_bucket`, and prints the
resolved endpoint and region.

### Upload a Directory

```sh
r2 upload-dir --source data --prefix raw --overwrite skip
```

Files are uploaded using their path relative to `--source`. With the example
above, `data/a/b.csv` becomes `raw/a/b.csv`.

| Flag | Notes |
| --- | --- |
| `--source` | Local directory to upload. Required. |
| `--bucket` | Override `R2_BUCKET`. |
| `--prefix` | Remote key prefix. Falls back to `R2_PREFIX`. |
| `--overwrite` | `skip`, `replace`, or `fail`. Defaults to `skip`. |
| `--exclude` | Filename to skip. Can be repeated. Defaults to `.DS_Store`. |
| `--dry-run` | Show planned transfers without uploading. |
| `--env-file` | Dotenv file to load. |

### Download a Prefix

```sh
r2 download-prefix --target data --prefix raw --strip-prefix
```

With `--strip-prefix`, `raw/a/b.csv` is saved as `data/a/b.csv`. With
`--preserve-key`, it is saved as `data/raw/a/b.csv`.

| Flag | Notes |
| --- | --- |
| `--target` | Local directory to write into. Required. |
| `--bucket` | Override `R2_BUCKET`. |
| `--prefix` | Remote key prefix. Falls back to `R2_PREFIX`. |
| `--preserve-key` / `--strip-prefix` | Preserve the full object key or remove the requested prefix. |
| `--overwrite` | `replace`, `skip`, or `fail`. Defaults to `replace`. |
| `--dry-run` | Show planned transfers without downloading. |
| `--env-file` | Dotenv file to load. |

### Single-Object Commands

```sh
r2 upload --bucket test-bucket --src README.md --key README.md
r2 download --bucket test-bucket --key README.md
```

These commands remain available for older scripts. Prefer `upload-dir` and
`download-prefix` for app directory workflows.

## 1Password

Use `op inject` when `env.example` contains 1Password item references:

```sh
op inject -i env.example -o .env
op run --env-file .env -- r2 doctor --show-bucket
```

Mounted 1Password dotenv files are supported because the package only consumes
environment variables and `.env` files.

## Python Usage

```python
from r2 import R2Settings, download_prefix, upload_directory, verify_bucket

settings = R2Settings(_env_file=".env")
verify_bucket(settings=settings)

upload_directory("data", prefix="raw", settings=settings)
download_prefix("downloads", prefix="raw", preserve_key=False, settings=settings)
```

For classes, transfer summaries, and compatibility helpers, see the
[API reference](api.md).

## App Integration

Delegate app-specific upload and download tasks to the package command:

```make
download:
  uv run r2 download-prefix --target data

upload:
  uv run r2 upload-dir --source data
```

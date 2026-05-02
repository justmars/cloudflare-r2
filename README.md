# cloudflare-r2

![Github CI](https://github.com/justmars/cloudflare-r2/actions/workflows/ci.yml/badge.svg)

Small Python and CLI wrapper for Cloudflare R2's S3-compatible API.

Use it when you want a reusable `r2` command for directory transfers, dotenv
configuration, and bucket access checks across apps.

## Install

```sh
uv add cloudflare-r2
```

## Configure

Create a `.env` file:

```sh
R2_ACCOUNT_ID=your-account-id
R2_BUCKET=your-bucket
R2_ACCESS_KEY_ID=your-token-key
R2_SECRET_ACCESS_KEY=your-token-secret
R2_REGION=auto
R2_PREFIX=
```

Then verify that credentials and bucket access work:

```sh
r2 doctor --env-file .env --show-bucket
```

## Common Commands

Upload a local directory:

```sh
r2 upload-dir --source data --prefix "" --overwrite skip
```

Download a remote prefix:

```sh
r2 download-prefix --target data --prefix "" --preserve-key
```

Single-object compatibility commands are still available:

```sh
r2 upload --bucket test-bucket --src README.md --key README.md
r2 download --bucket test-bucket --key README.md
```

## 1Password

Generate a local dotenv file from item references:

```sh
op inject -i env.example -o .env
op run --env-file .env -- r2 doctor --show-bucket
```

Mounted 1Password `.env` files work the same way because the package reads
normal environment variables and dotenv files.

## App Integration

Delegate app-specific upload and download tasks to the package command:

```make
download:
  uv run r2 download-prefix --target data

upload:
  uv run r2 upload-dir --source data
```

Full usage notes and API reference are published at
[justmars.github.io/cloudflare-r2](https://justmars.github.io/cloudflare-r2).

import click
from rich.console import Console
from rich.table import Table

from .cf import CloudflareR2Bucket
from .exceptions import R2Error
from .settings import R2Settings
from .transfer import download_prefix, upload_directory, verify_bucket

console = Console()


@click.group()
def cli():
    """Extensible wrapper of commands."""
    pass


def _settings(env_file: str | None) -> R2Settings:
    if env_file:
        return R2Settings(_env_file=env_file)  # type: ignore[call-arg]
    return R2Settings()


def _print_summary(summary) -> None:
    table = Table("Action", "Key", "Local path")
    for record in summary.records:
        table.add_row(record.action, record.key, str(record.local_path))
    console.print(table)
    console.print(
        f"{summary.planned} planned, {summary.transferred} transferred, "
        f"{summary.skipped} skipped"
    )


@cli.command()
@click.option("--env-file", type=click.Path(exists=True, dir_okay=False), default=None)
@click.option("--show-bucket", is_flag=True, help="Print the resolved bucket name.")
def doctor(env_file: str | None, show_bucket: bool):
    """Validate R2 settings and bucket access."""
    try:
        settings = _settings(env_file)
        verify_bucket(settings=settings)
    except R2Error as exc:
        raise click.ClickException(str(exc)) from exc
    console.print("R2 settings loaded and bucket access verified.")
    if show_bucket:
        console.print(f"bucket={settings.bucket_name}")
    console.print(f"endpoint_url={settings.endpoint_url}")
    console.print(f"region={settings.region}")


@cli.command()
@click.option(
    "--bucket",
    type=str,
    help="Cloudflare R2 bucket to source the file to be downloaded",
)
@click.option(
    "--key",
    type=str,
    help="filename in the cloud to be downloaded",
)
def download(bucket: str, key: str):
    """Given R2 `bucket`, retrieve file represented by `key`."""
    cf = CloudflareR2Bucket(name=bucket)
    console.print(f"Extracted bucket {cf=}")
    res = cf.get(key=key)
    console.print(f"Extracted {key=} from {cf=}")
    chunks = res["Body"].iter_chunks()  # type: ignore
    with open(key, "wb") as target_file:
        for chunk in chunks:
            target_file.write(chunk)
    console.print(f"Created {key=} locally.")


@cli.command()
@click.option(
    "--bucket",
    type=str,
    help="Cloudflare R2 bucket to upload the file.",
)
@click.option(
    "--src",
    type=str,
    help="Path to the local file to be uploaded.",
)
@click.option(
    "--key",
    type=str,
    help="filename to represent the local src file in the cloud.",
)
def upload(bucket: str, src: str, key: str):
    """Given R2 `bucket`, save file represented `src` to designated bucket `key`."""
    cf = CloudflareR2Bucket(name=bucket)
    console.print(f"Uploading {src=} to bucket {cf=} as {key=}")
    cf.upload(file_like=src, key=key)
    console.print(f"Uploaded {src=} as {key=}.")


@cli.command("upload-dir")
@click.option("--source", type=click.Path(exists=True, file_okay=False), required=True)
@click.option("--bucket", type=str, default=None, help="Override R2_BUCKET.")
@click.option("--prefix", type=str, default=None, help="Remote key prefix.")
@click.option(
    "--overwrite",
    type=click.Choice(["skip", "replace", "fail"]),
    default="skip",
    show_default=True,
)
@click.option("--exclude", multiple=True, default=(".DS_Store",), show_default=True)
@click.option("--dry-run", is_flag=True)
@click.option("--env-file", type=click.Path(exists=True, dir_okay=False), default=None)
def upload_dir(
    source: str,
    bucket: str | None,
    prefix: str | None,
    overwrite: str,
    exclude: tuple[str, ...],
    dry_run: bool,
    env_file: str | None,
):
    """Upload a local directory into an R2 prefix."""
    try:
        summary = upload_directory(
            source,
            bucket=bucket,
            prefix=prefix,
            overwrite=overwrite,  # type: ignore[arg-type]
            exclude=exclude,
            dry_run=dry_run,
            settings=_settings(env_file),
        )
    except R2Error as exc:
        raise click.ClickException(str(exc)) from exc
    _print_summary(summary)


@cli.command("download-prefix")
@click.option("--target", type=click.Path(file_okay=False), required=True)
@click.option("--bucket", type=str, default=None, help="Override R2_BUCKET.")
@click.option("--prefix", type=str, default=None, help="Remote key prefix.")
@click.option("--preserve-key/--strip-prefix", default=True, show_default=True)
@click.option(
    "--overwrite",
    type=click.Choice(["replace", "skip", "fail"]),
    default="replace",
    show_default=True,
)
@click.option("--dry-run", is_flag=True)
@click.option("--env-file", type=click.Path(exists=True, dir_okay=False), default=None)
def download_prefix_command(
    target: str,
    bucket: str | None,
    prefix: str | None,
    preserve_key: bool,
    overwrite: str,
    dry_run: bool,
    env_file: str | None,
):
    """Download objects under an R2 prefix into a local directory."""
    try:
        summary = download_prefix(
            target,
            bucket=bucket,
            prefix=prefix,
            preserve_key=preserve_key,
            overwrite=overwrite,  # type: ignore[arg-type]
            dry_run=dry_run,
            settings=_settings(env_file),
        )
    except R2Error as exc:
        raise click.ClickException(str(exc)) from exc
    _print_summary(summary)


if __name__ == "__main__":
    cli()  # search @cli.command

import click
from rich.console import Console

from .cf import CloudflareR2Bucket

console = Console()


@click.group()
def cli():
    """Extensible wrapper of commands."""
    pass


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


if __name__ == "__main__":
    cli()  # search @cli.command

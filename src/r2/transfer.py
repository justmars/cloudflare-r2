from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path, PurePosixPath
from typing import Literal

from botocore.exceptions import ClientError
from pydantic import BaseModel, ConfigDict, Field

from .exceptions import R2PathMappingError, R2SettingsError, R2TransferError
from .settings import R2Settings, normalize_prefix

UploadOverwrite = Literal["skip", "replace", "fail"]
DownloadOverwrite = Literal["replace", "skip", "fail"]
TransferAction = Literal[
    "upload",
    "download",
    "skip",
    "would_upload",
    "would_download",
    "replace",
    "would_replace",
]


class TransferRecord(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    key: str
    local_path: Path
    action: TransferAction
    size: int | None = None
    reason: str | None = None


class TransferSummary(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    bucket: str
    prefix: str
    dry_run: bool = False
    records: list[TransferRecord] = Field(default_factory=list)

    @property
    def planned(self) -> int:
        return len(self.records)

    @property
    def transferred(self) -> int:
        return sum(
            1
            for record in self.records
            if record.action in {"upload", "download", "replace"}
        )

    @property
    def skipped(self) -> int:
        return sum(1 for record in self.records if record.action == "skip")


def create_client(settings: R2Settings | None = None):
    import boto3

    resolved = settings or R2Settings()
    return boto3.client("s3", **resolved.boto3_kwargs())


def verify_bucket(settings: R2Settings | None = None, client=None) -> bool:
    from .exceptions import R2BucketAccessError

    resolved = settings or R2Settings()
    bucket = _resolve_bucket(None, resolved)
    s3 = client or create_client(resolved)
    try:
        s3.head_bucket(Bucket=bucket)
    except Exception as exc:  # boto3 raises several concrete botocore errors here.
        raise R2BucketAccessError(f"Unable to access R2 bucket {bucket!r}") from exc
    return True


def upload_directory(
    source_dir,
    *,
    bucket: str | None = None,
    prefix: str | None = None,
    overwrite: UploadOverwrite = "skip",
    exclude: Iterable[str] = (".DS_Store",),
    dry_run: bool = False,
    settings: R2Settings | None = None,
    client=None,
) -> TransferSummary:
    if overwrite not in {"skip", "replace", "fail"}:
        raise ValueError("overwrite must be one of: skip, replace, fail")

    resolved = settings or R2Settings()
    resolved_bucket = _resolve_bucket(bucket, resolved)
    resolved_prefix = normalize_prefix(
        prefix if prefix is not None else resolved.prefix
    )
    source = Path(source_dir)
    if not source.is_dir():
        raise R2PathMappingError(f"Source directory does not exist: {source}")

    s3 = client or create_client(resolved)
    excluded = set(exclude)
    records: list[TransferRecord] = []

    for local_path in sorted(path for path in source.rglob("*") if path.is_file()):
        if local_path.name in excluded:
            continue
        key = _upload_key(source, local_path, resolved_prefix)
        size = local_path.stat().st_size
        exists = _object_exists(s3, resolved_bucket, key)
        if exists and overwrite == "skip":
            records.append(
                TransferRecord(
                    key=key,
                    local_path=local_path,
                    action="skip",
                    size=size,
                    reason="remote object exists",
                )
            )
            continue
        if exists and overwrite == "fail":
            raise R2TransferError(f"Remote object already exists: {key}")
        action: TransferAction = "replace" if exists else "upload"
        if dry_run:
            records.append(
                TransferRecord(
                    key=key,
                    local_path=local_path,
                    action="would_replace" if exists else "would_upload",
                    size=size,
                )
            )
            continue
        if exists and overwrite == "replace":
            s3.delete_object(Bucket=resolved_bucket, Key=key)
        s3.upload_file(str(local_path), resolved_bucket, key)
        records.append(
            TransferRecord(key=key, local_path=local_path, action=action, size=size)
        )

    return TransferSummary(
        bucket=resolved_bucket,
        prefix=resolved_prefix,
        dry_run=dry_run,
        records=records,
    )


def download_prefix(
    target_dir,
    *,
    bucket: str | None = None,
    prefix: str | None = None,
    preserve_key: bool = True,
    overwrite: DownloadOverwrite = "replace",
    dry_run: bool = False,
    settings: R2Settings | None = None,
    client=None,
) -> TransferSummary:
    if overwrite not in {"replace", "skip", "fail"}:
        raise ValueError("overwrite must be one of: replace, skip, fail")

    resolved = settings or R2Settings()
    resolved_bucket = _resolve_bucket(bucket, resolved)
    resolved_prefix = normalize_prefix(
        prefix if prefix is not None else resolved.prefix
    )
    target = Path(target_dir)
    s3 = client or create_client(resolved)
    records: list[TransferRecord] = []

    for item in _iter_objects(s3, resolved_bucket, resolved_prefix):
        key = item["Key"]
        if key.endswith("/"):
            continue
        local_path = _download_path(target, key, resolved_prefix, preserve_key)
        exists = local_path.exists()
        if exists and overwrite == "skip":
            records.append(
                TransferRecord(
                    key=key,
                    local_path=local_path,
                    action="skip",
                    size=item.get("Size"),
                    reason="local file exists",
                )
            )
            continue
        if exists and overwrite == "fail":
            raise R2TransferError(f"Local file already exists: {local_path}")

        if dry_run:
            records.append(
                TransferRecord(
                    key=key,
                    local_path=local_path,
                    action="would_replace" if exists else "would_download",
                    size=item.get("Size"),
                )
            )
            continue

        local_path.parent.mkdir(parents=True, exist_ok=True)
        s3.download_file(resolved_bucket, key, str(local_path))
        records.append(
            TransferRecord(
                key=key,
                local_path=local_path,
                action="replace" if exists else "download",
                size=item.get("Size"),
            )
        )

    return TransferSummary(
        bucket=resolved_bucket,
        prefix=resolved_prefix,
        dry_run=dry_run,
        records=records,
    )


def _resolve_bucket(bucket: str | None, settings: R2Settings) -> str:
    resolved = bucket or settings.bucket_name
    if not resolved:
        raise R2SettingsError("R2 bucket is required. Set R2_BUCKET or pass bucket=.")
    return resolved


def _upload_key(source_dir: Path, local_path: Path, prefix: str) -> str:
    try:
        relative = local_path.relative_to(source_dir)
    except ValueError as exc:
        raise R2PathMappingError(f"{local_path} is not under {source_dir}") from exc
    key = PurePosixPath(*relative.parts).as_posix()
    if not key or key.startswith("../") or key == "..":
        raise R2PathMappingError(f"Invalid upload path mapping: {local_path}")
    return f"{prefix}{key}"


def _download_path(target_dir: Path, key: str, prefix: str, preserve_key: bool) -> Path:
    mapped_key = key if preserve_key else key.removeprefix(prefix)
    candidate = Path(*PurePosixPath(mapped_key).parts)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise R2PathMappingError(f"Invalid download path mapping: {key}")
    return target_dir / candidate


def _object_exists(client, bucket: str, key: str) -> bool:
    try:
        client.head_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code")
        if code in {"404", "NoSuchKey", "NotFound"}:
            return False
        raise
    return True


def _iter_objects(client, bucket: str, prefix: str):
    paginator = client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        yield from page.get("Contents", [])

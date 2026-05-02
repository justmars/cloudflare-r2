from .__main__ import cli
from .cf import CloudflareR2, CloudflareR2Bucket
from .exceptions import (
    R2BucketAccessError,
    R2Error,
    R2PathMappingError,
    R2SettingsError,
    R2TransferError,
)
from .logger import file_logging, setup_logging
from .settings import R2Settings
from .transfer import create_client, download_prefix, upload_directory, verify_bucket

file_logging()
setup_logging()

__all__ = [
    "CloudflareR2",
    "CloudflareR2Bucket",
    "R2BucketAccessError",
    "R2Error",
    "R2PathMappingError",
    "R2Settings",
    "R2SettingsError",
    "R2TransferError",
    "cli",
    "create_client",
    "download_prefix",
    "upload_directory",
    "verify_bucket",
]

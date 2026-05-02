class R2Error(Exception):
    """Base exception for cloudflare-r2 errors."""


class R2SettingsError(R2Error):
    """Raised when required R2 settings are missing or invalid."""


class R2BucketAccessError(R2Error):
    """Raised when the configured bucket cannot be reached."""


class R2TransferError(R2Error):
    """Raised when an upload or download transfer fails."""


class R2PathMappingError(R2Error):
    """Raised when a local path cannot be mapped to a valid object key."""

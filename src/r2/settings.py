from pathlib import Path
from typing import Any

from pydantic import AliasChoices, Field, SecretStr, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class R2Settings(BaseSettings):
    """Runtime settings for Cloudflare R2's S3-compatible API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    account_id: str = Field(
        validation_alias=AliasChoices("R2_ACCOUNT_ID", "CF_ACCT_ID")
    )
    bucket_name: str | None = Field(default=None, validation_alias="R2_BUCKET")
    access_key_id: SecretStr = Field(validation_alias="R2_ACCESS_KEY_ID")
    secret_access_key: SecretStr = Field(validation_alias="R2_SECRET_ACCESS_KEY")
    endpoint_url_override: str | None = Field(
        default=None, validation_alias="R2_ENDPOINT_URL"
    )
    region: str = Field(
        default="auto",
        validation_alias=AliasChoices("R2_REGION", "CF_R2_REGION"),
    )
    prefix: str = Field(default="", validation_alias="R2_PREFIX")

    @computed_field
    @property
    def endpoint_url(self) -> str:
        if self.endpoint_url_override:
            return self.endpoint_url_override.rstrip("/")
        return f"https://{self.account_id}.r2.cloudflarestorage.com"

    @property
    def normalized_prefix(self) -> str:
        return normalize_prefix(self.prefix)

    @property
    def bucket(self) -> str | None:
        return self.bucket_name

    def boto3_kwargs(self) -> dict[str, Any]:
        return {
            "endpoint_url": self.endpoint_url,
            "aws_access_key_id": self.access_key_id.get_secret_value(),
            "aws_secret_access_key": self.secret_access_key.get_secret_value(),
            "region_name": self.region,
        }

    def redacted_dict(self) -> dict[str, str | None]:
        return {
            "account_id": self.account_id,
            "bucket": self.bucket_name,
            "endpoint_url": self.endpoint_url,
            "region": self.region,
            "prefix": self.normalized_prefix,
            "access_key_id": self.access_key_id.get_secret_value()[:4] + "...",
            "secret_access_key": "**********",
        }


def normalize_prefix(prefix: str | None) -> str:
    if not prefix:
        return ""
    normalized = str(PurePosixish(prefix)).strip("/")
    return f"{normalized}/" if normalized else ""


class PurePosixish:
    def __init__(self, value: str | Path) -> None:
        self.value = str(value).replace("\\", "/")

    def __str__(self) -> str:
        while "//" in self.value:
            self.value = self.value.replace("//", "/")
        return self.value

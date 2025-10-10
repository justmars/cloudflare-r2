from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.r2.cf import CloudflareR2, CloudflareR2Bucket


@pytest.fixture
def mock_boto_resource():
    """Mock the boto3.resource() call globally."""
    with patch("boto3.resource") as mock_resource:
        yield mock_resource


def test_get_bucket(mock_boto_resource):
    mock_bucket = MagicMock()
    mock_boto_resource.return_value.Bucket.return_value = mock_bucket
    r2 = CloudflareR2(account_id="ACT")
    bucket = r2.get_bucket("test-bucket")
    assert bucket == mock_bucket


@pytest.fixture
def mock_bucket_obj():
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_bucket.meta.client = mock_client
    return mock_bucket, mock_client


def test_bucket_client(mock_boto_resource, mock_bucket_obj):
    mock_bucket, mock_client = mock_bucket_obj
    mock_boto_resource.return_value.Bucket.return_value = mock_bucket
    b = CloudflareR2Bucket(account_id="ACT", name="test-bucket")
    assert b.client is mock_client


def test_get_object_success(mock_boto_resource, mock_bucket_obj):
    mock_bucket, mock_client = mock_bucket_obj
    mock_boto_resource.return_value.Bucket.return_value = mock_bucket
    mock_client.get_object.return_value = {"Body": "data"}

    b = CloudflareR2Bucket(account_id="ACT", name="bucket")
    result = b.get("some/key.txt")
    assert result == {"Body": "data"}
    mock_client.get_object.assert_called_once_with(Bucket="bucket", Key="some/key.txt")


def test_get_object_failure(mock_boto_resource, mock_bucket_obj):
    mock_bucket, mock_client = mock_bucket_obj
    mock_boto_resource.return_value.Bucket.return_value = mock_bucket
    mock_client.get_object.side_effect = Exception("Not found")

    b = CloudflareR2Bucket(account_id="ACT", name="bucket")
    result = b.get("missing.txt")
    assert result is None


def test_filter_content():
    objects_list = [
        {"Key": "a/test.txt"},
        {"Key": "b/test.csv"},
        {"Key": "c/test.txt"},
    ]
    filtered = list(CloudflareR2Bucket.filter_content(".txt", objects_list))
    assert len(filtered) == 2
    assert all(obj["Key"].endswith(".txt") for obj in filtered)


def test_upload_and_download(tmp_path, mock_boto_resource, mock_bucket_obj):
    mock_bucket, _ = mock_bucket_obj
    mock_boto_resource.return_value.Bucket.return_value = mock_bucket

    b = CloudflareR2Bucket(account_id="ACT", name="bucket")

    # Create a temporary file to upload
    test_file = tmp_path / "file.txt"
    test_file.write_text("hello")

    # upload
    b.upload(test_file, key="remote.txt")
    mock_bucket.upload_fileobj.assert_called_once()

    # download
    b.download(key="remote.txt", local_file=str(tmp_path / "out.txt"))
    mock_bucket.download_fileobj.assert_called_once()

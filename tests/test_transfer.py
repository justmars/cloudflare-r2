from pathlib import Path

from botocore.exceptions import ClientError

from src.r2.settings import R2Settings
from src.r2.transfer import download_prefix, upload_directory


class FakePaginator:
    def __init__(self, pages):
        self.pages = pages

    def paginate(self, **kwargs):
        self.kwargs = kwargs
        yield from self.pages


class FakeS3Client:
    def __init__(self, *, existing=None, pages=None):
        self.existing = set(existing or [])
        self.pages = pages or []
        self.calls = []

    def head_object(self, **kwargs):
        self.calls.append(("head_object", kwargs))
        if kwargs["Key"] not in self.existing:
            raise ClientError({"Error": {"Code": "404"}}, "HeadObject")

    def delete_object(self, **kwargs):
        self.calls.append(("delete_object", kwargs))

    def upload_file(self, *args):
        self.calls.append(("upload_file", args))

    def download_file(self, *args):
        self.calls.append(("download_file", args))
        Path(args[2]).write_text("downloaded")

    def get_paginator(self, name):
        self.calls.append(("get_paginator", name))
        return FakePaginator(self.pages)


def settings():
    return R2Settings(
        account_id="acct",
        bucket_name="bucket",
        access_key_id="key",
        secret_access_key="secret",
    )


def test_directory_upload_discovers_nested_files_and_excludes_ds_store(tmp_path):
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "file.txt").write_text("hello")
    (tmp_path / ".DS_Store").write_text("ignored")
    client = FakeS3Client()

    summary = upload_directory(
        tmp_path,
        prefix="data",
        settings=settings(),
        client=client,
    )

    assert [record.key for record in summary.records] == ["data/nested/file.txt"]
    assert (
        "upload_file",
        (str(tmp_path / "nested" / "file.txt"), "bucket", "data/nested/file.txt"),
    ) in client.calls


def test_upload_overwrite_replace_checks_deletes_and_uploads(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "file.txt").write_text("hello")
    client = FakeS3Client(existing={"prefix/file.txt"})

    summary = upload_directory(
        source,
        prefix="prefix",
        overwrite="replace",
        settings=settings(),
        client=client,
    )

    assert summary.records[0].action == "replace"
    assert [call[0] for call in client.calls] == [
        "head_object",
        "delete_object",
        "upload_file",
    ]


def test_upload_dry_run_makes_no_write_calls(tmp_path):
    (tmp_path / "file.txt").write_text("hello")
    client = FakeS3Client()

    summary = upload_directory(
        tmp_path,
        dry_run=True,
        settings=settings(),
        client=client,
    )

    assert summary.records[0].action == "would_upload"
    assert all(call[0] != "upload_file" for call in client.calls)


def test_download_prefix_lists_pages_skips_markers_and_creates_parents(tmp_path):
    client = FakeS3Client(
        pages=[
            {
                "Contents": [
                    {"Key": "data/", "Size": 0},
                    {"Key": "data/a.txt", "Size": 1},
                ]
            },
            {"Contents": [{"Key": "data/nested/b.txt", "Size": 2}]},
        ]
    )

    summary = download_prefix(
        tmp_path,
        prefix="data",
        settings=settings(),
        client=client,
    )

    assert [record.key for record in summary.records] == [
        "data/a.txt",
        "data/nested/b.txt",
    ]
    assert (tmp_path / "data" / "nested" / "b.txt").exists()


def test_download_dry_run_makes_no_write_calls(tmp_path):
    client = FakeS3Client(pages=[{"Contents": [{"Key": "data/a.txt", "Size": 1}]}])

    summary = download_prefix(
        tmp_path,
        prefix="data",
        dry_run=True,
        settings=settings(),
        client=client,
    )

    assert summary.records[0].action == "would_download"
    assert all(call[0] != "download_file" for call in client.calls)

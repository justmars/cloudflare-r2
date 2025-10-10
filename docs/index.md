---
hide:
- navigation
- toc
---

# Cloudflare R2

Python wrapper on Cloudflare R2. See Cloudflare [API](https://developers.cloudflare.com/r2/examples/boto3/).

## Command Line

```sh
# upload a file to a bucket
r2 upload --bucket test-bucket --src README.md --key sample-file-name-prefix

# download a file from a bucket
r2 download --bucket test-bucket --key sample-file-name-prefix
```

## Access Bucket

::: src.r2.cf.CloudflareR2

## Common Actions on Bucket

::: src.r2.cf.CloudflareR2Bucket

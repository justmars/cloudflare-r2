from .__main__ import *
from .cf import CloudflareR2, CloudflareR2Bucket
from .logger import file_logging, setup_logging

file_logging()
setup_logging()

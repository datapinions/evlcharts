#!/usr/bin/env sh

set -x

# Get the right python. See https://github.com/GoogleCloudPlatform/gsutil/issues/1427
export CLOUDSDK_PYTHON=$(which python3)

gsutil -m rsync -r working/site gs://evl.datapinions.com

gsutil setmeta -h "Content-Type:text/html; charset=utf-8" gs://evl.datapinions.com/index.html

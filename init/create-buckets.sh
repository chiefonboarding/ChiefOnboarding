#!/bin/sh
set -e
awslocal() { aws --endpoint-url="${AWS_ENDPOINT_URL:-http://localhost:4566}" "$@"; }

awslocal s3 mb s3://my-bucket
awslocal s3api put-bucket-cors --bucket my-bucket --cors-configuration '{
  "CORSRules": [{"AllowedOrigins":["*"],"AllowedMethods":["GET","PUT","POST"],"AllowedHeaders":["*"]}]
}'
echo "buckets ready"

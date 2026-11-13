import json
import time
import boto3
from botocore.exceptions import ClientError, EndpointConnectionError

s3 = boto3.client("s3", endpoint_url="http://object-storage-server:9000",
                  aws_access_key_id="minioadmin", aws_secret_access_key="minioadmin",
                  region_name="us-east-1")
for attempt in range(60):
    try:
        s3.list_buckets()
        break
    except (ClientError, EndpointConnectionError):
        if attempt == 59:
            raise
        time.sleep(3)
for bucket in ("profile-pics", "documents"):
    try:
        s3.create_bucket(Bucket=bucket)
    except ClientError as error:
        if error.response["Error"]["Code"] not in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            raise
s3.put_bucket_policy(Bucket="profile-pics", Policy=json.dumps({
    "Version": "2012-10-17", "Statement": [{"Effect": "Allow", "Principal": {"AWS": ["*"]},
    "Action": ["s3:GetObject"], "Resource": ["arn:aws:s3:::profile-pics/*"]}]}))
try:
    s3.delete_bucket_policy(Bucket="documents")
except ClientError as error:
    if error.response["Error"]["Code"] != "NoSuchBucketPolicy":
        raise
s3.upload_file("/seed-images/blog_student_api_cover_1794421033024.jpg", "profile-pics", "avatar.jpg",
               ExtraArgs={"ContentType": "image/jpeg"})
print("Storage ready: profile-pics/avatar.jpg public; documents private.")
from pathlib import Path
report = Path("/bootstrap/minicloud-report.pdf")
if report.exists():
    s3.upload_file(str(report), "documents", "minicloud-report.pdf", ExtraArgs={"ContentType": "application/pdf"})
    print("Uploaded technical report to documents/minicloud-report.pdf")

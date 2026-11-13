import hashlib
from pathlib import Path
import boto3
import urllib.request
import urllib.error

s3 = boto3.client('s3', endpoint_url='http://object-storage-server:9000',
                  aws_access_key_id='minioadmin', aws_secret_access_key='minioadmin', region_name='us-east-1')
for bucket, key in [('profile-pics', 'avatar.jpg'), ('documents', 'minicloud-report.pdf')]:
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = obj['Body'].read()
    assert len(data) > 100, key
    if key.endswith('.pdf'):
        assert data.startswith(b'%PDF-')
        assert hashlib.sha256(data).digest() == hashlib.sha256(Path('/bootstrap/minicloud-report.pdf').read_bytes()).digest()
    print(f'PASS authenticated download {bucket}/{key}: {len(data)} bytes')
url = 'http://object-storage-server:9000/documents/minicloud-report.pdf'
try:
    urllib.request.urlopen(url)
    raise AssertionError('Private report unexpectedly public')
except urllib.error.HTTPError as error:
    assert error.code == 403, error.code
    print('PASS anonymous report download denied with 403')

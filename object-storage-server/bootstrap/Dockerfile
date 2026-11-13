FROM python:3.11-alpine
RUN pip install --no-cache-dir boto3
WORKDIR /bootstrap
COPY init.py .
CMD ["python", "init.py"]

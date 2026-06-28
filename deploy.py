import argparse
import logging
import mimetypes
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from config import SITE_DIR, INDEX_DOCUMENT, ERROR_DOCUMENT

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


class StaticWebsiteDeployer:
    def __init__(self, bucket_name: str, region: str = None):
        self.bucket_name = bucket_name
        self.region = region
        session = boto3.Session(region_name=region) if region else boto3.Session()
        self.s3 = session.resource("s3")
        self.s3_client = session.client("s3")

    def deploy(self):
        self._ensure_bucket_exists()
        self._configure_website_hosting()
        self._upload_site()
        self._print_website_url()

    def _ensure_bucket_exists(self):
        bucket = self.s3.Bucket(self.bucket_name)
        try:
            bucket.load()
            logger.info(f"Bucket already exists: {self.bucket_name}")
        except ClientError as exc:
            error_code = exc.response["Error"]["Code"]
            if error_code == "404":
                logger.info(f"Creating bucket: {self.bucket_name}")
                self._create_bucket()
            else:
                raise

    def _create_bucket(self):
        params = {"Bucket": self.bucket_name}
        if self.region and self.region != "us-east-1":
            params["CreateBucketConfiguration"] = {"LocationConstraint": self.region}
        self.s3_client.create_bucket(**params)
        self.s3_client.put_bucket_policy(
            Bucket=self.bucket_name,
            Policy=self._public_read_policy(),
        )

    def _configure_website_hosting(self):
        logger.info("Configuring S3 static website hosting...")
        self.s3_client.put_bucket_website(
            Bucket=self.bucket_name,
            WebsiteConfiguration={
                "IndexDocument": {"Suffix": INDEX_DOCUMENT},
                "ErrorDocument": {"Key": ERROR_DOCUMENT},
            },
        )
        self.s3_client.put_bucket_policy(
            Bucket=self.bucket_name,
            Policy=self._public_read_policy(),
        )

    def _upload_site(self):
        logger.info(f"Uploading files from {SITE_DIR}...")
        if not SITE_DIR.exists():
            raise FileNotFoundError(f"Site directory not found: {SITE_DIR}")

        for path in sorted(SITE_DIR.rglob("*")):
            if path.is_file():
                key = str(path.relative_to(SITE_DIR)).replace("\\", "/")
                self._upload_file(path, key)

    def _upload_file(self, source_path: Path, key: str):
        content_type, _ = mimetypes.guess_type(str(source_path))
        if content_type is None:
            content_type = "application/octet-stream"

        logger.info(f"Uploading {key} ({content_type})")
        self.s3_client.upload_file(
            Filename=str(source_path),
            Bucket=self.bucket_name,
            Key=key,
            ExtraArgs={"ContentType": content_type, "ACL": "public-read"},
        )

    def _print_website_url(self):
        region_suffix = "" if self.region in (None, "us-east-1") else f"-{self.region}"
        website_url = f"http://{self.bucket_name}.s3-website{region_suffix}.amazonaws.com"
        logger.info("\nWebsite deployed successfully!")
        logger.info(f"Static website URL: {website_url}")

    def _public_read_policy(self) -> str:
        return (
            '{'
            '"Version":"2012-10-17",'
            '"Statement":[{'
            '"Sid":"PublicReadGetObject",'
            '"Effect":"Allow",'
            '"Principal":"*",'
            '"Action":["s3:GetObject"],'
            f'"Resource":["arn:aws:s3:::{self.bucket_name}/*"]'
            '}]'
            '}'
        )


def parse_args():
    parser = argparse.ArgumentParser(description="Deploy a static website to Amazon S3.")
    parser.add_argument("--bucket", required=True, help="Unique S3 bucket name")
    parser.add_argument("--region", default=None, help="AWS region for the bucket (example: us-east-1)")
    return parser.parse_args()


def main():
    args = parse_args()
    deployer = StaticWebsiteDeployer(bucket_name=args.bucket, region=args.region)
    deployer.deploy()


if __name__ == "__main__":
    main()

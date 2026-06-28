# AWS Static Website Framework

This repository contains a minimal Python framework for deploying a static website to Amazon S3.

## What it includes

- `deploy.py`: deploys a local `site/` directory to an S3 bucket and configures static website hosting.
- `site/`: sample static website content.
- `requirements.txt`: Python dependency list.

## Setup

1. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```

2. Configure AWS credentials:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `AWS_DEFAULT_REGION`

   Or use the AWS CLI profile system.

3. Choose a unique S3 bucket name.

## Usage

Deploy the website:

```bash
python deploy.py --bucket your-unique-bucket-name --region us-east-1
```

The script will:

- create the S3 bucket if it does not exist
- enable static website hosting
- upload files from `site/`
- print the website endpoint URL

## Customization

Replace files in `site/` with your own HTML, CSS, or assets.

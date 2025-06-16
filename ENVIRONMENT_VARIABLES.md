# Environment Variables

This document describes all environment variables used by the CloudWatch Logs Analyzer application.

## AWS Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `AWS_REGION` | AWS region to use for CloudWatch API calls | `us-east-1` | Yes |
| `AWS_PROFILE` | AWS profile to use from credentials file | `default` | No |
| `AWS_SDK_LOAD_CONFIG` | Whether to load config from AWS config file | `1` | No |
| `AWS_ACCESS_KEY_ID` | AWS access key ID (not recommended, use profile instead) | - | No |
| `AWS_SECRET_ACCESS_KEY` | AWS secret access key (not recommended, use profile instead) | - | No |

## Application Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `STREAMLIT_SERVER_PORT` | Port for Streamlit server | `8501` | No |
| `STREAMLIT_SERVER_HEADLESS` | Run Streamlit in headless mode | `true` | No |
| `LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` | No |
| `MAX_LOG_ENTRIES` | Maximum number of log entries to fetch | `10000` | No |
| `DEFAULT_TIME_RANGE_HOURS` | Default time range in hours for log queries | `24` | No |

## Docker-specific Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PYTHONDONTWRITEBYTECODE` | Prevent Python from writing .pyc files | `1` | No |
| `PYTHONUNBUFFERED` | Force Python to run in unbuffered mode | `1` | No |

## Usage Examples

### Docker Run with Environment Variables

```bash
docker run -p 8501:8501 \
  -v ~/.aws:/home/appuser/.aws:ro \
  -e AWS_REGION=us-west-2 \
  -e AWS_PROFILE=production \
  -e LOG_LEVEL=DEBUG \
  -e MAX_LOG_ENTRIES=20000 \
  cloudwatch-logs-analyzer
```

### Docker Compose

```yaml
version: '3'
services:
  app:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ~/.aws:/home/appuser/.aws:ro
    environment:
      - AWS_REGION=us-west-2
      - AWS_PROFILE=production
      - LOG_LEVEL=INFO
      - MAX_LOG_ENTRIES=10000
```

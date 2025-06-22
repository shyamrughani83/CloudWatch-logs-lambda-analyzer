# CloudWatch Logs Analyzer

A powerful tool for analyzing AWS CloudWatch logs with advanced visualization and insights built with Amazon Q CLI.
Get it for [free](https://community.aws/builderid?trk=529c4ce9-0395-4c42-915a-d70bf060ef3c&sc_channel=el)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Multi-log Group Analysis**: Select and analyze multiple log groups simultaneously
- **Performance Metrics**: Visualize Lambda function performance metrics
- **Error Analysis**: Identify and analyze errors in your logs
- **Memory Usage Optimization**: Get insights into memory usage patterns
- **Interactive Visualizations**: Explore your logs with interactive charts and filters
- **Docker Support**: Easy deployment with Docker

## Prerequisites

- Docker installed
- AWS credentials configured in ~/.aws/credentials

## Quick Start

### Build the Docker image

```bash
docker build -t cloudwatch-logs-analyzer .
```

### Run the container

```bash
docker run -p 8501:8501 \
  -v ~/.aws:/home/appuser/.aws:ro \
  -e AWS_REGION=us-east-1 \
  -e AWS_SDK_LOAD_CONFIG=1 \
  cloudwatch-logs-analyzer
```

### Access the application

Open your browser and navigate to: http://localhost:8501

## AWS Credentials

The application securely accesses your AWS credentials from the standard `~/.aws/credentials` file. The credentials are mounted as read-only inside the container.

Make sure your AWS credentials file has the correct permissions:

```bash
chmod 600 ~/.aws/credentials
```

## Customization

You can customize the deployment by setting environment variables:

```bash
docker run -p 8501:8501 \
  -v ~/.aws:/home/appuser/.aws:ro \
  -e AWS_REGION=us-west-2 \
  -e AWS_SDK_LOAD_CONFIG=1 \
  -e AWS_PROFILE=myprofile \
  cloudwatch-logs-analyzer
```

For a complete list of environment variables, see [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md).

## Security Features

- Multi-stage build to reduce attack surface
- Non-root user for running the application
- Read-only mounting of AWS credentials

For more information about security, see our [Security Policy](SECURITY.md).

## Contributing

Contributions are welcome! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

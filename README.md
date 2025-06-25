# CloudWatch Logs & Lambda Analyzer

A powerful tool for analyzing AWS CloudWatch logs and Lambda functions with advanced visualization and insights built with Amazon Q CLI.
Get it for [free](https://community.aws/builderid?trk=529c4ce9-0395-4c42-915a-d70bf060ef3c&sc_channel=el)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- **Multi-log Group Analysis**: Select and analyze multiple log groups simultaneously
- **Lambda Function Integration**: Invoke and monitor Lambda functions directly from the web interface
- **Performance Metrics**: Visualize Lambda function performance metrics including duration, memory usage, and invocation counts
- **Error Analysis**: Identify and analyze errors in your logs with intelligent pattern recognition
- **Memory Usage Optimization**: Get insights into memory usage patterns and recommendations for optimization
- **Cost Analysis**: Track and analyze Lambda function costs based on invocation patterns
- **Interactive Visualizations**: Explore your logs with interactive charts and filters
- **Real-time Monitoring**: Monitor Lambda function executions in real-time
- **Custom Alerts**: Set up custom alerts based on log patterns or Lambda metrics
- **Docker Support**: Easy deployment with Docker

## Prerequisites

- Docker installed
- AWS credentials configured in ~/.aws/credentials
- Appropriate IAM permissions for CloudWatch Logs and Lambda functions

## Quick Start

### Build the Docker image

```bash
docker build -t cloudwatch-logs-lambda-analyzer .
```

### Run the container

```bash
docker run -p 8501:8501 \
  -v ~/.aws:/home/appuser/.aws:ro \
  -e AWS_REGION=us-east-1 \
  -e AWS_SDK_LOAD_CONFIG=1 \
  cloudwatch-logs-lambda-analyzer
```

### Access the application

Open your browser and navigate to: http://localhost:8501

## Lambda Function Integration

The CloudWatch Logs & Lambda Analyzer allows you to interact with your Lambda functions directly from the web interface:

1. **Invoke Lambda Functions**: Test your Lambda functions with custom payloads
2. **View Execution Results**: See the response, logs, and execution metrics in real-time
3. **Monitor Performance**: Track invocation counts, duration, and memory usage over time
4. **Analyze Cold Starts**: Identify and analyze cold start patterns in your Lambda functions
5. **Debug Errors**: Quickly identify and debug errors in your Lambda function executions

To use the Lambda integration:

1. Select the "Lambda Functions" tab in the sidebar
2. Choose a Lambda function from the dropdown
3. Configure the test payload (if required)
4. Click "Invoke Function" to execute and view results

## AWS Credentials

The application securely accesses your AWS credentials from the standard `~/.aws/credentials` file. The credentials are mounted as read-only inside the container.

Make sure your AWS credentials file has the correct permissions:

```bash
chmod 600 ~/.aws/credentials
```

## Required IAM Permissions

For full functionality, your AWS credentials should have the following permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "logs:DescribeLogGroups",
                "logs:DescribeLogStreams",
                "logs:GetLogEvents",
                "logs:FilterLogEvents",
                "lambda:ListFunctions",
                "lambda:GetFunction",
                "lambda:InvokeFunction",
                "lambda:GetFunctionConfiguration",
                "cloudwatch:GetMetricData",
                "cloudwatch:GetMetricStatistics"
            ],
            "Resource": "*"
        }
    ]
}
```

## Customization

You can customize the deployment by setting environment variables:

```bash
docker run -p 8501:8501 \
  -v ~/.aws:/home/appuser/.aws:ro \
  -e AWS_REGION=us-west-2 \
  -e AWS_SDK_LOAD_CONFIG=1 \
  -e AWS_PROFILE=myprofile \
  -e LAMBDA_TIMEOUT=30 \
  -e MAX_LOG_ENTRIES=1000 \
  cloudwatch-logs-lambda-analyzer
```

For a complete list of environment variables, see [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md).

## Security Features

- Multi-stage build to reduce attack surface
- Non-root user for running the application
- Read-only mounting of AWS credentials
- Secure handling of Lambda function payloads
- No persistent storage of sensitive information

For more information about security, see our [Security Policy](SECURITY.md).

## Contributing

Contributions are welcome! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

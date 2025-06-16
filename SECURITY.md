# Security Policy

## Supported Versions

Use this section to tell people about which versions of your project are currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of CloudWatch Logs Analyzer seriously. If you believe you've found a security vulnerability, please follow these steps:

1. **Do not disclose the vulnerability publicly**
2. **Email the details to [INSERT SECURITY EMAIL]**
   - Provide a detailed description of the vulnerability
   - Include steps to reproduce the issue
   - Mention the version of the application where you found the vulnerability
   - If possible, include suggestions for remediation

## What to Expect

- We will acknowledge receipt of your vulnerability report within 48 hours
- We will provide a more detailed response within 7 days with our assessment and planned next steps
- We will work with you to understand and address the issue
- We will keep you informed about our progress towards a fix
- Once the vulnerability is fixed, we will publicly acknowledge your responsible disclosure (unless you prefer to remain anonymous)

## Security Measures

CloudWatch Logs Analyzer implements several security measures:

1. **AWS Credentials Handling**
   - AWS credentials are never stored within the application
   - Credentials are accessed securely from the standard AWS credentials file
   - When using Docker, credentials are mounted as read-only

2. **Docker Security**
   - Multi-stage build to reduce attack surface
   - Non-root user for running the application
   - Minimal base image (python:3.9-slim)

3. **Data Security**
   - No persistent storage of log data beyond the current session
   - All data processing happens locally within the application

## Security Best Practices for Users

1. Ensure your AWS credentials have the minimum required permissions
2. Use IAM roles with temporary credentials when possible
3. Regularly rotate your AWS access keys
4. Set proper file permissions on your AWS credentials file (chmod 600)
5. Keep the application and its dependencies updated to the latest versions

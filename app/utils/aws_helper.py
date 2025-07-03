import boto3
from botocore.exceptions import ClientError, NoCredentialsError, ProfileNotFound
import pandas as pd
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_boto3_session(region, profile=None):
    """Create a boto3 session with the specified region and profile"""
    try:
        if profile:
            logger.info(f"Creating AWS session with profile '{profile}' in region '{region}'")
            session = boto3.Session(region_name=region, profile_name=profile)
        else:
            logger.info(f"Creating AWS session with default profile in region '{region}'")
            session = boto3.Session(region_name=region)
        return session
    except ProfileNotFound:
        logger.error(f"AWS profile '{profile}' not found")
        raise Exception(f"AWS profile '{profile}' not found")
    except Exception as e:
        logger.error(f"Failed to create AWS session: {str(e)}")
        raise Exception(f"Failed to create AWS session: {str(e)}")

def test_aws_connection(region, profile=None):
    """Test AWS connection by listing log groups"""
    try:
        session = get_boto3_session(region, profile)
        logs_client = session.client('logs')
        
        # Try to list log groups (limited to 1) to test connection
        logs_client.describe_log_groups(limit=1)
        
        logger.info(f"Successfully connected to AWS in region {region}")
        return {
            'success': True,
            'message': 'Successfully connected to AWS'
        }
    except NoCredentialsError:
        logger.error("No AWS credentials found")
        return {
            'success': False,
            'error': 'No AWS credentials found. Please configure your AWS credentials.'
        }
    except ClientError as e:
        logger.error(f"AWS API error: {e.response['Error']['Message']}")
        return {
            'success': False,
            'error': f"AWS API error: {e.response['Error']['Message']}"
        }
    except Exception as e:
        logger.error(f"Error testing AWS connection: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def get_log_groups(region, profile=None):
    """Get all CloudWatch log groups with optimized performance"""
    logger.info(f"Fetching log groups from region {region}")
    session = get_boto3_session(region, profile)
    logs_client = session.client('logs')
    
    log_groups = []
    paginator = logs_client.get_paginator('describe_log_groups')
    
    # Use a smaller page size for faster initial response
    page_iterator = paginator.paginate(
        PaginationConfig={
            'MaxItems': 100,
            'PageSize': 20
        }
    )
    
    for page in page_iterator:
        for log_group in page['logGroups']:
            log_groups.append({
                'name': log_group['logGroupName'],
                'arn': log_group.get('arn', ''),
                'storedBytes': log_group.get('storedBytes', 0),
                'creationTime': datetime.datetime.fromtimestamp(
                    log_group['creationTime'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
            })
    
    logger.info(f"Found {len(log_groups)} log groups")
    return log_groups

def get_lambda_functions(region, profile=None):
    """Get all Lambda functions with detailed information and optimized performance"""
    logger.info(f"Fetching Lambda functions from region {region}")
    session = get_boto3_session(region, profile)
    lambda_client = session.client('lambda')
    
    functions = []
    paginator = lambda_client.get_paginator('list_functions')
    
    # Use a smaller page size for faster initial response
    page_iterator = paginator.paginate(
        PaginationConfig={
            'MaxItems': 100,
            'PageSize': 20
        }
    )
    
    for page in page_iterator:
        for function in page['Functions']:
            # Extract basic information without additional API calls
            functions.append({
                'name': function['FunctionName'],
                'arn': function['FunctionArn'],
                'runtime': function.get('Runtime', 'N/A'),
                'memory': function.get('MemorySize', 0),
                'timeout': function.get('Timeout', 0),
                'lastModified': function.get('LastModified', 'N/A'),
                'handler': function.get('Handler', 'N/A'),
                'description': function.get('Description', ''),
                'role': function.get('Role', 'N/A'),
                'environment': function.get('Environment', {}).get('Variables', {}),
                'codeSize': function.get('CodeSize', 0),
                'version': function.get('Version', '$LATEST'),
                'state': function.get('State', 'N/A'),
                'lastUpdateStatus': function.get('LastUpdateStatus', 'N/A')
            })
    
    logger.info(f"Found {len(functions)} Lambda functions")
    return functions

def get_log_events(region, log_group_name, log_stream_name, profile=None):
    """Get log events for a specific log group and stream"""
    logger.info(f"Fetching log events for {log_group_name}/{log_stream_name}")
    session = get_boto3_session(region, profile)
    logs_client = session.client('logs')
    
    events = []
    
    # Instead of using a paginator, we'll handle pagination manually
    # since get_log_events requires nextToken instead of using standard pagination
    next_token = None
    
    try:
        while True:
            # Prepare parameters
            params = {
                'logGroupName': log_group_name,
                'logStreamName': log_stream_name,
                'startFromHead': True,
                'limit': 50  # Fetch 50 events at a time
            }
            
            # Add nextToken if we have one
            if next_token:
                params['nextToken'] = next_token
            
            # Make the API call
            response = logs_client.get_log_events(**params)
            
            # Process events
            for event in response.get('events', []):
                events.append({
                    'timestamp': datetime.datetime.fromtimestamp(
                        event['timestamp'] / 1000).strftime('%Y-%m-%d %H:%M:%S'),
                    'message': event['message']
                })
            
            # Check if we need to continue pagination
            if response.get('nextForwardToken') == next_token:
                # We've reached the end of the stream
                break
            
            next_token = response.get('nextForwardToken')
            
            # Limit the number of events to prevent excessive API calls
            if len(events) >= 1000:
                logger.info(f"Reached maximum event limit (1000) for {log_group_name}/{log_stream_name}")
                break
    
    except Exception as e:
        logger.error(f"Error fetching log events: {str(e)}")
        raise
    
    logger.info(f"Found {len(events)} log events")
    return events

def invoke_lambda_function(region, function_name, payload, profile=None):
    """Invoke a Lambda function with the specified payload"""
    logger.info(f"Invoking Lambda function {function_name}")
    session = get_boto3_session(region, profile)
    lambda_client = session.client('lambda')
    
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=payload,
            LogType='Tail'  # Include logs in the response
        )
        
        # Read the response payload
        payload_bytes = response['Payload'].read()
        payload_str = payload_bytes.decode('utf-8')
        
        # Get the logs if available
        log_result = response.get('LogResult', '')
        
        logger.info(f"Lambda function {function_name} invoked successfully")
        return {
            'statusCode': response['StatusCode'],
            'payload': payload_str,
            'executedVersion': response.get('ExecutedVersion', 'N/A'),
            'logResult': log_result
        }
    except ClientError as e:
        logger.error(f"Error invoking Lambda function {function_name}: {e.response['Error']['Message']}")
        return {
            'error': f"AWS API error: {e.response['Error']['Message']}"
        }
    except Exception as e:
        logger.error(f"Error invoking Lambda function {function_name}: {str(e)}")
        return {
            'error': str(e)
        }

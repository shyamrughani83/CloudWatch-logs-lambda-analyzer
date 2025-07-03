"""
Lambda Function Test Tool

A standalone tool for testing AWS Lambda functions with various event templates.
"""

import streamlit as st
import boto3
import json
import base64
import datetime
import time
import uuid
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError

# Set page configuration
st.set_page_config(
    page_title="Lambda Function Test Tool",
    page_icon="⚡",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    background: linear-gradient(135deg, #232F3E 0%, #0D1218 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 10px;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
.main-header h1 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    color: white;
}
.main-header p {
    font-size: 1rem;
    opacity: 0.9;
    color: white;
}
.aws-badge {
    background-color: #FF9900;
    color: #232F3E;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
    font-weight: 600;
    display: inline-block;
    margin-top: 0.5rem;
}
.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
    padding: 0.75rem 1rem;
    border-radius: 8px 8px 0 0;
}
.stTabs [aria-selected="true"] {
    background-color: #FF9900 !important;
    color: #232F3E !important;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# Main header
st.markdown("""
<div class="main-header">
    <h1>⚡ Lambda Function Test Tool</h1>
    <p>Test AWS Lambda functions with various event templates</p>
    <div class="aws-badge">Powered by AWS</div>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'aws_region' not in st.session_state:
    st.session_state.aws_region = 'us-east-1'

if 'aws_profile' not in st.session_state:
    st.session_state.aws_profile = 'default'

if 'test_events' not in st.session_state:
    st.session_state.test_events = {}

# AWS Connection settings
st.sidebar.header("AWS Connection")

# Region selection
available_regions = [
    'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
    'ca-central-1',
    'eu-north-1', 'eu-west-1', 'eu-west-2', 'eu-west-3', 'eu-central-1',
    'ap-northeast-1', 'ap-northeast-2', 'ap-northeast-3',
    'ap-southeast-1', 'ap-southeast-2',
    'ap-south-1',
    'sa-east-1'
]

# Get AWS profiles
def get_aws_profiles():
    import os
    import configparser
    
    profiles = ['default']
    aws_credentials_path = os.path.expanduser('~/.aws/credentials')
    aws_config_path = os.path.expanduser('~/.aws/config')
    
    # Check credentials file
    if os.path.exists(aws_credentials_path):
        config = configparser.ConfigParser()
        config.read(aws_credentials_path)
        profiles.extend([s.replace('profile ', '') for s in config.sections() if s != 'default'])
    
    # Check config file
    if os.path.exists(aws_config_path):
        config = configparser.ConfigParser()
        config.read(aws_config_path)
        profiles.extend([s.replace('profile ', '') for s in config.sections() if s != 'default' and s.startswith('profile ')])
    
    # Remove duplicates and sort
    return sorted(list(set(profiles)))

available_profiles = get_aws_profiles()

selected_region = st.sidebar.selectbox(
    "AWS Region",
    options=available_regions,
    index=available_regions.index(st.session_state.aws_region),
    key="region_selector"
)

selected_profile = st.sidebar.selectbox(
    "AWS Profile",
    options=available_profiles,
    index=available_profiles.index(st.session_state.aws_profile) if st.session_state.aws_profile in available_profiles else 0,
    key="profile_selector"
)

# Update session state when region or profile changes
if selected_region != st.session_state.aws_region or selected_profile != st.session_state.aws_profile:
    st.session_state.aws_region = selected_region
    st.session_state.aws_profile = selected_profile

# Create AWS session
try:
    session = boto3.Session(
        region_name=selected_region,
        profile_name=None if selected_profile == "default" else selected_profile
    )
    lambda_client = session.client('lambda')
    st.sidebar.success(f"Connected to AWS in {selected_region}")
except Exception as e:
    st.sidebar.error(f"Failed to connect to AWS: {str(e)}")
    lambda_client = None

# Function to get Lambda functions
def get_lambda_functions():
    try:
        functions = []
        paginator = lambda_client.get_paginator('list_functions')
        
        for page in paginator.paginate():
            functions.extend(page.get('Functions', []))
        
        return functions
    except Exception as e:
        st.error(f"Failed to list Lambda functions: {str(e)}")
        return []

# Function to invoke Lambda
def invoke_lambda(function_name, payload, invocation_type="RequestResponse"):
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType=invocation_type,
            LogType='Tail' if invocation_type == 'RequestResponse' else 'None',
            Payload=payload
        )
        
        result = {
            'StatusCode': response.get('StatusCode'),
            'ExecutedVersion': response.get('ExecutedVersion')
        }
        
        # If there's a payload in the response, decode it
        if 'Payload' in response:
            payload_bytes = response['Payload'].read()
            if payload_bytes:
                try:
                    result['Response'] = json.loads(payload_bytes.decode('utf-8'))
                except:
                    result['Response'] = payload_bytes.decode('utf-8')
        
        # Check for function error
        if response.get('FunctionError'):
            result['FunctionError'] = response.get('FunctionError')
        
        # Get logs from the response if available
        if 'LogResult' in response:
            try:
                log_result = base64.b64decode(response['LogResult']).decode('utf-8')
                result['LogResult'] = log_result
            except Exception as e:
                result['LogError'] = f"Failed to decode log result: {str(e)}"
        
        return result
    except Exception as e:
        return {'error': str(e)}

# Function to get event templates
def get_event_template(template_name):
    templates = {
        "Custom": {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        },
        "API Gateway AWS Proxy": {
            "resource": "/path/to/resource",
            "path": "/path/to/resource",
            "httpMethod": "GET",
            "headers": {
                "Accept": "*/*",
                "Host": "example.execute-api.us-east-1.amazonaws.com"
            },
            "queryStringParameters": {
                "param1": "value1",
                "param2": "value2"
            },
            "pathParameters": {
                "id": "123"
            },
            "stageVariables": {
                "stageVar1": "value1"
            },
            "requestContext": {
                "accountId": "123456789012",
                "resourceId": "abcdef",
                "stage": "prod",
                "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
                "identity": {
                    "sourceIp": "192.168.0.1"
                },
                "resourcePath": "/path/to/resource",
                "httpMethod": "GET",
                "apiId": "1234567890"
            },
            "body": "{\"message\": \"Hello from Lambda!\"}"
        },
        "CloudWatch Logs": {
            "awslogs": {
                "data": "BASE64ENCODED_DATA"
            }
        },
        "CloudWatch Scheduled Event": {
            "id": "cdc73f9d-aea9-11e3-9d5a-835b769c0d9c",
            "detail-type": "Scheduled Event",
            "source": "aws.events",
            "account": "123456789012",
            "time": "1970-01-01T00:00:00Z",
            "region": "us-east-1",
            "resources": [
                "arn:aws:events:us-east-1:123456789012:rule/ExampleRule"
            ],
            "detail": {}
        },
        "DynamoDB Update": {
            "Records": [
                {
                    "eventID": "1",
                    "eventVersion": "1.0",
                    "dynamodb": {
                        "Keys": {
                            "Id": {
                                "N": "101"
                            }
                        },
                        "NewImage": {
                            "Message": {
                                "S": "New item!"
                            },
                            "Id": {
                                "N": "101"
                            }
                        },
                        "StreamViewType": "NEW_AND_OLD_IMAGES",
                        "SequenceNumber": "111",
                        "SizeBytes": 26
                    },
                    "awsRegion": "us-east-1",
                    "eventName": "INSERT",
                    "eventSourceARN": "arn:aws:dynamodb:us-east-1:123456789012:table/ExampleTable/stream/2015-06-27T00:48:05.899",
                    "eventSource": "aws:dynamodb"
                }
            ]
        },
        "S3 Put": {
            "Records": [
                {
                    "eventVersion": "2.0",
                    "eventSource": "aws:s3",
                    "awsRegion": "us-east-1",
                    "eventTime": "1970-01-01T00:00:00.000Z",
                    "eventName": "ObjectCreated:Put",
                    "userIdentity": {
                        "principalId": "EXAMPLE"
                    },
                    "requestParameters": {
                        "sourceIPAddress": "127.0.0.1"
                    },
                    "responseElements": {
                        "x-amz-request-id": "EXAMPLE123456789",
                        "x-amz-id-2": "EXAMPLE123/5678abcdefghijklambdaisawesome/mnopqrstuvwxyzABCDEFGH"
                    },
                    "s3": {
                        "s3SchemaVersion": "1.0",
                        "configurationId": "testConfigRule",
                        "bucket": {
                            "name": "example-bucket",
                            "ownerIdentity": {
                                "principalId": "EXAMPLE"
                            },
                            "arn": "arn:aws:s3:::example-bucket"
                        },
                        "object": {
                            "key": "test/key",
                            "size": 1024,
                            "eTag": "0123456789abcdef0123456789abcdef",
                            "sequencer": "0A1B2C3D4E5F678901"
                        }
                    }
                }
            ]
        },
        "SNS Notification": {
            "Records": [
                {
                    "EventVersion": "1.0",
                    "EventSubscriptionArn": "arn:aws:sns:us-east-1:123456789012:sns-topic:00000000-0000-0000-0000-000000000000",
                    "EventSource": "aws:sns",
                    "Sns": {
                        "SignatureVersion": "1",
                        "Timestamp": "1970-01-01T00:00:00.000Z",
                        "Signature": "EXAMPLE",
                        "SigningCertUrl": "EXAMPLE",
                        "MessageId": "95df01b4-ee98-5cb9-9903-4c221d41eb5e",
                        "Message": "Hello from SNS!",
                        "MessageAttributes": {
                            "Test": {
                                "Type": "String",
                                "Value": "TestString"
                            },
                            "TestBinary": {
                                "Type": "Binary",
                                "Value": "TestBinary"
                            }
                        },
                        "Type": "Notification",
                        "UnsubscribeUrl": "EXAMPLE",
                        "TopicArn": "arn:aws:sns:us-east-1:123456789012:sns-topic",
                        "Subject": "TestInvoke"
                    }
                }
            ]
        },
        "SQS Message": {
            "Records": [
                {
                    "messageId": "19dd0b57-b21e-4ac1-bd88-01bbb068cb78",
                    "receiptHandle": "MessageReceiptHandle",
                    "body": "Hello from SQS!",
                    "attributes": {
                        "ApproximateReceiveCount": "1",
                        "SentTimestamp": "1523232000000",
                        "SenderId": "123456789012",
                        "ApproximateFirstReceiveTimestamp": "1523232000001"
                    },
                    "messageAttributes": {},
                    "md5OfBody": "7b270e59b47ff90a553787216d55d91d",
                    "eventSource": "aws:sqs",
                    "eventSourceARN": "arn:aws:sqs:us-east-1:123456789012:MyQueue",
                    "awsRegion": "us-east-1"
                }
            ]
        }
    }
    
    return templates.get(template_name, templates["Custom"])

# Main content
if lambda_client:
    # Get Lambda functions
    functions = get_lambda_functions()
    
    if functions:
        # Create tabs for Quick Test and Saved Events
        tab1, tab2 = st.tabs(["🧪 Quick Test", "💾 Saved Events"])
        
        # Quick Test tab
        with tab1:
            st.subheader("Test Lambda Function")
            
            # Function selection
            function_names = [func.get('FunctionName', '') for func in functions]
            selected_function = st.selectbox(
                "Select Lambda Function",
                function_names,
                key="function_selector"
            )
            
            # Template selection
            template_options = [
                "Custom",
                "API Gateway AWS Proxy",
                "CloudWatch Logs",
                "CloudWatch Scheduled Event",
                "DynamoDB Update",
                "S3 Put",
                "SNS Notification",
                "SQS Message"
            ]
            
            selected_template = st.selectbox(
                "Event Template",
                template_options,
                key="template_selector"
            )
            
            # Generate template JSON
            template_json = get_event_template(selected_template)
            
            # JSON editor
            st.markdown("#### Event Payload (JSON)")
            payload_json = st.text_area(
                "Edit the JSON payload",
                value=json.dumps(template_json, indent=2),
                height=300,
                key="payload_editor"
            )
            
            # Validate JSON
            valid_json = True
            try:
                if payload_json:
                    json.loads(payload_json)
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {str(e)}")
                valid_json = False
            
            # Invocation type
            col1, col2 = st.columns([2, 1])
            
            with col1:
                invocation_type = st.radio(
                    "Invocation Type",
                    ["RequestResponse", "Event", "DryRun"],
                    horizontal=True,
                    help="RequestResponse: Synchronous invocation, Event: Asynchronous invocation, DryRun: Validate parameters without executing"
                )
            
            with col2:
                # Save event option
                save_event = st.checkbox("Save this event for later use")
                if save_event:
                    event_name = st.text_input("Event Name", key="save_event_name")
            
            # Test button
            if st.button("Test Function", type="primary", disabled=not valid_json):
                if save_event and not event_name:
                    st.error("Please provide a name for the event to save it.")
                else:
                    with st.spinner(f"Invoking {selected_function}..."):
                        # Save event if requested
                        if save_event and event_name:
                            if selected_function not in st.session_state.test_events:
                                st.session_state.test_events[selected_function] = []
                            
                            # Check if we already have 10 events
                            if len(st.session_state.test_events[selected_function]) >= 10:
                                st.warning("You can create up to 10 test events per function. The oldest event will be replaced.")
                                # Remove the oldest event
                                st.session_state.test_events[selected_function].pop(0)
                            
                            # Add new event
                            new_event = {
                                "id": str(uuid.uuid4()),
                                "name": event_name,
                                "json": payload_json,
                                "created_at": time.time()
                            }
                            
                            st.session_state.test_events[selected_function].append(new_event)
                            st.success(f"Test event '{event_name}' saved successfully!")
                        
                        # Invoke function
                        result = invoke_lambda(
                            function_name=selected_function,
                            payload=payload_json,
                            invocation_type=invocation_type
                        )
                        
                        # Display result
                        st.markdown("### Invocation Result")
                        
                        # Status code
                        status_code = result.get('StatusCode', 0)
                        if status_code >= 200 and status_code < 300:
                            st.success(f"Status Code: {status_code}")
                        else:
                            st.error(f"Status Code: {status_code}")
                        
                        # Check for function error
                        if 'FunctionError' in result:
                            st.error(f"Function Error: {result['FunctionError']}")
                        elif 'error' in result:
                            st.error(f"Error: {result['error']}")
                        
                        # Create tabs for response and logs
                        result_tab1, result_tab2 = st.tabs(["Response", "Logs"])
                        
                        # Response tab
                        with result_tab1:
                            if 'Response' in result:
                                if isinstance(result['Response'], dict) or isinstance(result['Response'], list):
                                    st.json(result['Response'])
                                else:
                                    st.code(result['Response'], language="text")
                            else:
                                st.info("No response data available.")
                            
                            # Display executed version
                            if 'ExecutedVersion' in result:
                                st.info(f"Executed Version: {result['ExecutedVersion']}")
                        
                        # Logs tab
                        with result_tab2:
                            # Display logs from the response if available
                            if 'LogResult' in result:
                                st.markdown("#### Execution Logs")
                                st.code(result['LogResult'], language="text")
                            elif 'LogError' in result:
                                st.error(result['LogError'])
                            else:
                                st.info("No logs available. This could be due to the invocation type.")
        
        # Saved Events tab
        with tab2:
            st.subheader("Saved Test Events")
            
            # Function selection
            function_names = [func.get('FunctionName', '') for func in functions]
            selected_function = st.selectbox(
                "Select Lambda Function",
                function_names,
                key="saved_function_selector"
            )
            
            # Display saved events for the selected function
            if selected_function in st.session_state.test_events and st.session_state.test_events[selected_function]:
                st.markdown(f"#### Events for {selected_function}")
                
                # Display events in a table
                for i, event in enumerate(st.session_state.test_events[selected_function]):
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.markdown(f"**{i+1}. {event['name']}**")
                            st.caption(f"Created: {datetime.datetime.fromtimestamp(event['created_at']).strftime('%Y-%m-%d %H:%M:%S')}")
                        
                        with col2:
                            if st.button("Run", key=f"run_{event['id']}"):
                                with st.spinner("Invoking Lambda function..."):
                                    try:
                                        # Invoke Lambda function
                                        result = invoke_lambda(
                                            function_name=selected_function,
                                            payload=event['json']
                                        )
                                        
                                        # Display result
                                        st.markdown("#### Invocation Result")
                                        
                                        # Status code
                                        status_code = result.get('StatusCode', 0)
                                        if status_code >= 200 and status_code < 300:
                                            st.success(f"Status Code: {status_code}")
                                        else:
                                            st.error(f"Status Code: {status_code}")
                                        
                                        # Check for function error
                                        if 'FunctionError' in result:
                                            st.error(f"Function Error: {result['FunctionError']}")
                                        elif 'error' in result:
                                            st.error(f"Error: {result['error']}")
                                        
                                        # Create tabs for response and logs
                                        result_tab1, result_tab2 = st.tabs(["Response", "Logs"])
                                        
                                        # Response tab
                                        with result_tab1:
                                            if 'Response' in result:
                                                if isinstance(result['Response'], dict) or isinstance(result['Response'], list):
                                                    st.json(result['Response'])
                                                else:
                                                    st.code(result['Response'], language="text")
                                            else:
                                                st.info("No response data available.")
                                        
                                        # Logs tab
                                        with result_tab2:
                                            # Display logs from the response if available
                                            if 'LogResult' in result:
                                                st.markdown("#### Execution Logs")
                                                st.code(result['LogResult'], language="text")
                                            else:
                                                st.info("No logs available.")
                                    except Exception as e:
                                        st.error(f"Error invoking function: {str(e)}")
                        
                        with col3:
                            if st.button("Delete", key=f"delete_{event['id']}"):
                                # Remove event
                                st.session_state.test_events[selected_function] = [
                                    e for e in st.session_state.test_events[selected_function] 
                                    if e['id'] != event['id']
                                ]
                                st.experimental_rerun()
                        
                        # Show event JSON in expander
                        with st.expander("Event JSON", expanded=False):
                            st.code(event['json'], language="json")
                        
                        st.markdown("---")
            else:
                st.info(f"No saved test events for {selected_function}. Create test events in the 'Quick Test' tab.")
    else:
        st.warning("No Lambda functions found in the selected region.")
else:
    st.error("Failed to connect to AWS. Please check your credentials and region.")

# Footer
st.markdown("""
<div style="margin-top: 3rem; text-align: center; font-size: 0.9rem; color: #545B64; padding: 1rem; border-top: 1px solid #eaeaea;">
    <p>Lambda Function Test Tool | Powered by AWS</p>
    <p>© 2025 | CloudWatch Logs & Lambda Analyzer</p>
</div>
""", unsafe_allow_html=True)

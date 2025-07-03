"""
Lambda Test Events component for CloudWatch Logs Analyzer.
Allows creating, managing, and running test events for Lambda functions.
"""

import streamlit as st
import json
import boto3
import time
import uuid
from typing import Dict, Any, List, Optional
from botocore.exceptions import ClientError

def render_lambda_test_events(lambda_client):
    """
    Render the Lambda test events interface.
    
    Args:
        lambda_client: Lambda client instance
    """
    st.markdown("""
    <div class="stcard">
        <h3>⚡ Lambda Test Events</h3>
        <p>Create and manage test events for your Lambda functions. You can create up to 10 test events per function.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if Lambda client is authenticated
    if not lambda_client or not lambda_client.is_authenticated():
        st.warning("Please connect to AWS to use this feature.")
        return
    
    # Get available Lambda functions
    try:
        functions = lambda_client.list_functions()
        function_names = [function['FunctionName'] for function in functions]
        
        if not function_names:
            st.info("No Lambda functions found in this region.")
            return
            
        # Select Lambda function
        selected_function = st.selectbox(
            "Select Lambda Function",
            function_names,
            key="test_events_function_selector"
        )
        
        if not selected_function:
            st.info("Please select a Lambda function.")
            return
            
        # Get function details
        function_details = lambda_client.get_function(selected_function)
        
        # Display function info
        with st.expander("Function Details", expanded=False):
            st.json(function_details)
        
        # Tabs for Test Events and Results
        tab1, tab2 = st.tabs(["Test Events", "Test Results"])
        
        # Test Events Tab
        with tab1:
            # Get existing test events from session state
            if 'test_events' not in st.session_state:
                st.session_state.test_events = {}
            
            if selected_function not in st.session_state.test_events:
                st.session_state.test_events[selected_function] = []
            
            # Create new test event
            st.subheader("Create Test Event")
            
            # Test event name
            event_name = st.text_input("Event Name", key="new_event_name")
            
            # Test event template selection
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
                "Template",
                template_options,
                key="event_template"
            )
            
            # Generate template JSON based on selection
            template_json = get_event_template(selected_template)
            
            # JSON editor for event payload
            event_json = st.text_area(
                "Event JSON",
                value=json.dumps(template_json, indent=2),
                height=300,
                key="event_json"
            )
            
            # Validate JSON
            try:
                json.loads(event_json)
                json_valid = True
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {str(e)}")
                json_valid = False
            
            # Save test event button
            col1, col2 = st.columns([1, 1])
            
            with col1:
                if st.button("Save Test Event", disabled=not event_name or not json_valid):
                    # Check if we already have 10 events
                    if len(st.session_state.test_events[selected_function]) >= 10:
                        st.error("You can create up to 10 test events per function. Please delete some events first.")
                    else:
                        # Add new event
                        new_event = {
                            "id": str(uuid.uuid4()),
                            "name": event_name,
                            "json": event_json,
                            "created_at": time.time()
                        }
                        
                        st.session_state.test_events[selected_function].append(new_event)
                        st.success(f"Test event '{event_name}' saved successfully!")
                        
                        # Clear inputs
                        st.session_state.new_event_name = ""
                        st.session_state.event_json = json.dumps(template_json, indent=2)
            
            with col2:
                if st.button("Test Function", disabled=not json_valid):
                    with st.spinner("Invoking Lambda function..."):
                        try:
                            # Invoke Lambda function
                            response = lambda_client.invoke_function(
                                function_name=selected_function,
                                payload=event_json
                            )
                            
                            # Store result in session state
                            if 'test_results' not in st.session_state:
                                st.session_state.test_results = []
                            
                            # Add result
                            result = {
                                "function_name": selected_function,
                                "event_name": event_name if event_name else "Unnamed Event",
                                "timestamp": time.time(),
                                "response": response,
                                "payload": event_json
                            }
                            
                            st.session_state.test_results.insert(0, result)
                            
                            # Show success message
                            st.success("Function invoked successfully! See results in the Test Results tab.")
                        except Exception as e:
                            st.error(f"Error invoking function: {str(e)}")
            
            # Display saved test events
            st.subheader("Saved Test Events")
            
            if not st.session_state.test_events[selected_function]:
                st.info("No saved test events for this function.")
            else:
                # Display events in a table
                for i, event in enumerate(st.session_state.test_events[selected_function]):
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.markdown(f"**{i+1}. {event['name']}**")
                        
                        with col2:
                            if st.button("Run", key=f"run_{event['id']}"):
                                with st.spinner("Invoking Lambda function..."):
                                    try:
                                        # Invoke Lambda function
                                        response = lambda_client.invoke_function(
                                            function_name=selected_function,
                                            payload=event['json']
                                        )
                                        
                                        # Store result in session state
                                        if 'test_results' not in st.session_state:
                                            st.session_state.test_results = []
                                        
                                        # Add result
                                        result = {
                                            "function_name": selected_function,
                                            "event_name": event['name'],
                                            "timestamp": time.time(),
                                            "response": response,
                                            "payload": event['json']
                                        }
                                        
                                        st.session_state.test_results.insert(0, result)
                                        
                                        # Show success message
                                        st.success("Function invoked successfully! See results in the Test Results tab.")
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
        
        # Test Results Tab
        with tab2:
            st.subheader("Test Results")
            
            if 'test_results' not in st.session_state or not st.session_state.test_results:
                st.info("No test results available. Run a test event to see results here.")
            else:
                # Filter results for the selected function
                function_results = [
                    result for result in st.session_state.test_results
                    if result['function_name'] == selected_function
                ]
                
                if not function_results:
                    st.info(f"No test results available for {selected_function}.")
                else:
                    # Display results
                    for i, result in enumerate(function_results):
                        with st.container():
                            st.markdown(f"**Test {i+1}: {result['event_name']}**")
                            st.markdown(f"*Executed at: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result['timestamp']))}*")
                            
                            # Display response details
                            response = result['response']
                            
                            # Status code
                            status_code = response.get('StatusCode', 0)
                            status_color = "green" if status_code == 200 else "red"
                            
                            st.markdown(f"Status Code: <span style='color:{status_color};font-weight:bold;'>{status_code}</span>", unsafe_allow_html=True)
                            
                            # Function error
                            if 'FunctionError' in response:
                                st.error(f"Function Error: {response['FunctionError']}")
                            
                            # Response tabs
                            resp_tab1, resp_tab2, resp_tab3 = st.tabs(["Response", "Logs", "Request"])
                            
                            with resp_tab1:
                                # Response payload
                                if 'Payload' in response:
                                    try:
                                        payload = response['Payload'].read().decode('utf-8')
                                        try:
                                            # Try to parse as JSON
                                            payload_json = json.loads(payload)
                                            st.json(payload_json)
                                        except:
                                            # Display as text
                                            st.text(payload)
                                    except:
                                        st.warning("Could not decode response payload")
                                else:
                                    st.info("No response payload")
                            
                            with resp_tab2:
                                # Log output
                                if 'LogResult' in response:
                                    try:
                                        import base64
                                        log_result = base64.b64decode(response['LogResult']).decode('utf-8')
                                        st.text(log_result)
                                    except:
                                        st.warning("Could not decode log result")
                                else:
                                    st.info("No log output available")
                            
                            with resp_tab3:
                                # Request payload
                                st.subheader("Request Payload")
                                try:
                                    request_json = json.loads(result['payload'])
                                    st.json(request_json)
                                except:
                                    st.text(result['payload'])
                            
                            st.markdown("---")
                    
                    # Clear results button
                    if st.button("Clear Test Results"):
                        st.session_state.test_results = [
                            result for result in st.session_state.test_results
                            if result['function_name'] != selected_function
                        ]
                        st.success("Test results cleared!")
                        st.experimental_rerun()
                
    except Exception as e:
        st.error(f"Error: {str(e)}")


def get_event_template(template_name: str) -> Dict:
    """
    Get a template for a Lambda test event.
    
    Args:
        template_name: Name of the template
        
    Returns:
        Dictionary with the template JSON
    """
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

"""
Lambda Functions component for CloudWatch Logs Analyzer.
Displays and manages Lambda functions.
"""

import streamlit as st
import pandas as pd
import json
import datetime
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional
from utils.lambda_client import LambdaClient
from utils.logger import get_logger

# Initialize logger
logger = get_logger("lambda_functions")

def render_lambda_functions(lambda_client: Optional[LambdaClient] = None) -> None:
    """
    Render Lambda functions management interface.
    
    Args:
        lambda_client: Optional LambdaClient instance
    """
    st.markdown("""
    <div class="stcard">
        <h3>⚡ Lambda Functions</h3>
    """, unsafe_allow_html=True)
    
    # Check if user has explicitly connected to AWS
    if 'aws_connected' not in st.session_state or not st.session_state.aws_connected:
        st.warning("Please click 'Connect to AWS' in the sidebar to view and manage Lambda functions.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    if not lambda_client or not lambda_client.is_authenticated():
        st.warning("AWS connection failed. Please check your credentials and try connecting again.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Fetch Lambda functions
    with st.spinner("Fetching Lambda functions..."):
        functions = lambda_client.list_functions()
    
    if not functions:
        st.info("No Lambda functions found in the current region.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Create a DataFrame for the functions
    functions_df = pd.DataFrame([
        {
            'Name': func.get('FunctionName', ''),
            'Runtime': func.get('Runtime', ''),
            'Memory (MB)': func.get('MemorySize', 0),
            'Timeout (s)': func.get('Timeout', 0),
            'Last Modified': func.get('LastModified', ''),
            'ARN': func.get('FunctionArn', '')
        }
        for func in functions
    ])
    
    # Display functions in a searchable table
    st.subheader("Available Functions")
    
    # Add search box
    search_term = st.text_input("Search functions", "")
    
    # Filter functions based on search term
    if search_term:
        filtered_df = functions_df[functions_df['Name'].str.contains(search_term, case=False)]
    else:
        filtered_df = functions_df
    
    # Display the table with an Actions column
    if not filtered_df.empty:
        # Create a copy of the DataFrame for display
        display_df = filtered_df.copy()
        
        # Add an Actions column with buttons
        st.write("### Lambda Functions")
        
        # Create a table-like display with columns
        cols = st.columns([3, 2, 1, 1, 2])
        cols[0].write("**Name**")
        cols[1].write("**Runtime**")
        cols[2].write("**Memory**")
        cols[3].write("**Timeout**")
        cols[4].write("**Actions**")
        
        st.markdown("<hr>", unsafe_allow_html=True)
        
        # Display each function with an Actions button
        for i, row in filtered_df.iterrows():
            cols = st.columns([3, 2, 1, 1, 2])
            cols[0].write(f"**{row['Name']}**")
            cols[1].write(f"{row['Runtime']}")
            cols[2].write(f"{row['Memory (MB)']} MB")
            cols[3].write(f"{row['Timeout (s)']} sec")
            
            # Add Test Events button in the Actions column
            if cols[4].button("Test Events", key=f"test_btn_{row['Name']}"):
                # Store the selected function name in session state
                st.session_state.selected_test_function = row['Name']
                # Show the test function dialog
                st.session_state.show_test_dialog = True
            
            st.markdown("<hr>", unsafe_allow_html=True)
    
    # Display the table
    if not filtered_df.empty:
        # Add an Actions column to the DataFrame
        actions_df = filtered_df.copy()
        
        # Display the dataframe with the original columns
        st.dataframe(
            filtered_df[['Name', 'Runtime', 'Memory (MB)', 'Timeout (s)', 'Last Modified']],
            use_container_width=True
        )
        
        # Create a separate section for Actions
        st.subheader("Actions")
        
        # Create a container for each function with action buttons
        for i, row in filtered_df.iterrows():
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"**{row['Name']}**")
                
                with col2:
                    # Add a view details button
                    if st.button("View Details", key=f"view_btn_{row['Name']}"):
                        st.session_state.selected_function = row['Name']
                        st.experimental_rerun()
                
                with col3:
                    # Add a test events button
                    if st.button("Test Events", key=f"test_btn_{row['Name']}"):
                        # Store the selected function name in session state
                        st.session_state.selected_test_function = row['Name']
                        # Show the test function dialog
                        st.session_state.show_test_dialog = True
                
                st.markdown("---")
        
        # Check if we should show the test dialog
        if 'show_test_dialog' in st.session_state and st.session_state.show_test_dialog and 'selected_test_function' in st.session_state:
            # Create a pop-up like container for test events
            st.markdown("""
            <style>
            .test-popup {
                background-color: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                margin: 20px 0;
                border: 1px solid #ddd;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="test-popup">', unsafe_allow_html=True)
            st.markdown(f"### Test Events: {st.session_state.selected_test_function}")
            
            # Create tabs for Quick Test and Saved Events
            test_tab1, test_tab2 = st.tabs(["Create Test Event", "Saved Events"])
            
            # Quick Test tab
            with test_tab1:
                # Event name input
                event_name = st.text_input("Event Name", key="event_name_input")
                
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
                    "Template",
                    template_options,
                    key="template_selector"
                )
                
                # Generate template JSON based on selection
                template_json = get_event_template(selected_template)
                
                # Test payload input
                st.markdown("#### Event JSON")
                test_payload = st.text_area(
                    "Edit the JSON payload",
                    value=json.dumps(template_json, indent=2),
                    height=200,
                    key="test_payload_area"
                )
                
                # Validate JSON
                valid_json = True
                try:
                    if test_payload:
                        json.loads(test_payload)
                except json.JSONDecodeError:
                    st.error("Invalid JSON payload")
                    valid_json = False
                
                # Action buttons
                col1, col2, col3 = st.columns([1, 1, 1])
                
                with col1:
                    # Save event button
                    if st.button("Save Event", key="save_event_btn", disabled=not valid_json or not event_name):
                        # Initialize test events in session state if not exists
                        if 'test_events' not in st.session_state:
                            st.session_state.test_events = {}
                        
                        if st.session_state.selected_test_function not in st.session_state.test_events:
                            st.session_state.test_events[st.session_state.selected_test_function] = []
                        
                        # Check if we already have 10 events
                        if len(st.session_state.test_events[st.session_state.selected_test_function]) >= 10:
                            st.error("You can create up to 10 test events per function. Please delete some events first.")
                        else:
                            # Add new event
                            import uuid
                            import time
                            new_event = {
                                "id": str(uuid.uuid4()),
                                "name": event_name,
                                "json": test_payload,
                                "created_at": time.time()
                            }
                            
                            st.session_state.test_events[st.session_state.selected_test_function].append(new_event)
                            st.success(f"Test event '{event_name}' saved successfully!")
                
                with col2:
                    # Invoke function button
                    if st.button("Invoke Function", key="invoke_test_btn", disabled=not valid_json):
                        with st.spinner(f"Invoking {st.session_state.selected_test_function}..."):
                            try:
                                payload = json.loads(test_payload) if test_payload else {}
                                result = lambda_client.invoke_function(
                                    function_name=st.session_state.selected_test_function,
                                    payload=payload,
                                    invocation_type="RequestResponse",
                                    fetch_logs=True
                                )
                                
                                # Store result in session state
                                st.session_state.test_result = result
                                
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
                                
                                # Create tabs for response and logs
                                response_tab, logs_tab = st.tabs(["Response", "Logs"])
                                
                                # Response tab
                                with response_tab:
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
                                with logs_tab:
                                    # Display logs from the response if available
                                    if 'LogResult' in result:
                                        st.markdown("#### Execution Logs")
                                        st.code(result['LogResult'], language="text")
                                    
                                    # Display CloudWatch logs if available
                                    if 'CloudWatchLogs' in result and result['CloudWatchLogs']:
                                        st.markdown("#### CloudWatch Logs")
                                        
                                        # Create a formatted log output
                                        log_output = ""
                                        for log in result['CloudWatchLogs']:
                                            timestamp = datetime.datetime.fromtimestamp(log.get('timestamp', 0)/1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                                            message = log.get('message', '')
                                            log_output += f"{timestamp} - {message}\n"
                                        
                                        st.code(log_output, language="text")
                                    
                                    # If no logs are available
                                    if 'LogResult' not in result and 'CloudWatchLogs' not in result:
                                        st.info("No logs available. This could be due to the invocation type or log retention settings.")
                                
                            except Exception as e:
                                st.error(f"Error invoking function: {str(e)}")
                
                with col3:
                    # Close button
                    if st.button("Close", key="close_test_btn"):
                        st.session_state.show_test_dialog = False
                        st.experimental_rerun()
            
            # Saved Events tab
            with test_tab2:
                st.markdown("#### Saved Test Events")
                st.info("An event is an input to your Lambda function. You can create up to 10 test events per function. Saved events are stored and are preserved if you switch browsers or machines.")
                
                # Initialize test events in session state if not exists
                if 'test_events' not in st.session_state:
                    st.session_state.test_events = {}
                
                if st.session_state.selected_test_function not in st.session_state.test_events:
                    st.session_state.test_events[st.session_state.selected_test_function] = []
                
                # Display saved events
                if st.session_state.test_events[st.session_state.selected_test_function]:
                    for i, event in enumerate(st.session_state.test_events[st.session_state.selected_test_function]):
                        with st.container():
                            col1, col2, col3 = st.columns([3, 1, 1])
                            
                            with col1:
                                st.markdown(f"**{i+1}. {event['name']}**")
                            
                            with col2:
                                if st.button("Run", key=f"run_{event['id']}"):
                                    with st.spinner("Invoking Lambda function..."):
                                        try:
                                            # Invoke Lambda function
                                            result = lambda_client.invoke_function(
                                                function_name=st.session_state.selected_test_function,
                                                payload=json.loads(event['json']),
                                                invocation_type="RequestResponse",
                                                fetch_logs=True
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
                                            
                                            # Create tabs for response and logs
                                            response_tab, logs_tab = st.tabs(["Response", "Logs"])
                                            
                                            # Response tab
                                            with response_tab:
                                                if 'Response' in result:
                                                    if isinstance(result['Response'], dict) or isinstance(result['Response'], list):
                                                        st.json(result['Response'])
                                                    else:
                                                        st.code(result['Response'], language="text")
                                                else:
                                                    st.info("No response data available.")
                                            
                                            # Logs tab
                                            with logs_tab:
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
                                    st.session_state.test_events[st.session_state.selected_test_function] = [
                                        e for e in st.session_state.test_events[st.session_state.selected_test_function] 
                                        if e['id'] != event['id']
                                    ]
                                    st.experimental_rerun()
                            
                            # Show event JSON in expander
                            with st.expander("Event JSON", expanded=False):
                                st.code(event['json'], language="json")
                            
                            st.markdown("---")
                else:
                    st.info("No saved test events for this function yet. Create test events in the 'Create Test Event' tab.")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Function details and management
        st.subheader("Function Details")
        
        # Determine which function to show details for
        if 'selected_function' in st.session_state:
            selected_function = st.session_state.selected_function
        else:
            # Select a function to view details
            selected_function = st.selectbox(
                "Select a function to view details",
                filtered_df['Name'].tolist()
            )
        
        if selected_function:
            display_function_details(lambda_client, selected_function)
    else:
        st.info("No functions match your search criteria.")
    
    st.markdown("</div>", unsafe_allow_html=True)


def display_function_details(lambda_client: LambdaClient, function_name: str) -> None:
    """
    Display details for a selected Lambda function.
    
    Args:
        lambda_client: LambdaClient instance
        function_name: Name of the Lambda function
    """
    # Create tabs for different function views
    tabs = st.tabs(["Overview", "Configuration", "Permissions", "Test Function"])
    
    # Get function details
    with st.spinner(f"Fetching details for {function_name}..."):
        function_details = lambda_client.get_function(function_name)
    
    if not function_details:
        st.error(f"Failed to fetch details for {function_name}")
        return
    
    # Extract configuration
    config = function_details.get('Configuration', {})
    
    # Overview tab
    with tabs[0]:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">⚡</div>
                <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 500;">Function Name</div>
                <div style="font-size: 1.4rem; font-weight: 700; margin-bottom: 0.25rem; color: #007bff;">{function_name}</div>
                <div style="font-size: 0.8rem; color: #6c757d;">Runtime: {config.get('Runtime', 'N/A')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">🧠</div>
                <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 500;">Memory</div>
                <div style="font-size: 1.4rem; font-weight: 700; margin-bottom: 0.25rem; color: #007bff;">{config.get('MemorySize', 'N/A')} MB</div>
                <div style="font-size: 0.8rem; color: #6c757d;">Timeout: {config.get('Timeout', 'N/A')} seconds</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Function ARN and other details
        st.markdown("### Function Details")
        st.code(config.get('FunctionArn', 'N/A'), language="text")
        
        # Last modified and version
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Last Modified", config.get('LastModified', 'N/A').split('T')[0])
        with col2:
            st.metric("Version", config.get('Version', 'N/A'))
        
        # Environment variables
        st.markdown("### Environment Variables")
        env_vars = config.get('Environment', {}).get('Variables', {})
        if env_vars:
            # Create a DataFrame for environment variables
            env_df = pd.DataFrame([
                {'Key': key, 'Value': value}
                for key, value in env_vars.items()
            ])
            st.dataframe(env_df, use_container_width=True)
        else:
            st.info("No environment variables defined.")
    
    # Configuration tab
    with tabs[1]:
        st.markdown("### Function Configuration")
        
        # Memory size slider
        current_memory = config.get('MemorySize', 128)
        new_memory = st.slider(
            "Memory Size (MB)",
            min_value=128,
            max_value=10240,
            value=current_memory,
            step=64,
            help="Amount of memory available to the function during execution"
        )
        
        # Timeout slider
        current_timeout = config.get('Timeout', 3)
        new_timeout = st.slider(
            "Timeout (seconds)",
            min_value=1,
            max_value=900,
            value=current_timeout,
            step=1,
            help="Maximum execution time for the function"
        )
        
        # Update configuration button
        if st.button("Update Configuration"):
            if new_memory != current_memory or new_timeout != current_timeout:
                with st.spinner("Updating function configuration..."):
                    result = lambda_client.update_function_configuration(
                        function_name=function_name,
                        memory_size=new_memory,
                        timeout=new_timeout
                    )
                
                if 'error' in result:
                    st.error(f"Failed to update configuration: {result['error']}")
                else:
                    st.success("Function configuration updated successfully!")
                    st.experimental_rerun()
            else:
                st.info("No changes to apply.")
    
    # Permissions tab
    with tabs[2]:
        st.markdown("### Function Permissions")
        
        # Get function policy
        with st.spinner("Fetching function policies..."):
            function_policy = lambda_client.get_function_policy(function_name)
            role_policies = lambda_client.get_function_role_policy(function_name)
        
        # Display execution role
        st.markdown("#### Execution Role")
        st.code(config.get('Role', 'N/A'), language="text")
        
        # Display attached policies
        st.markdown("#### Attached Policies")
        attached_policies = role_policies.get('attached_policies', [])
        if attached_policies:
            for policy in attached_policies:
                st.markdown(f"- {policy.get('PolicyName', 'Unknown')}")
        else:
            st.info("No attached policies found.")
        
        # Display inline policies
        st.markdown("#### Inline Policies")
        inline_policies = role_policies.get('inline_policies', [])
        if inline_policies:
            for policy in inline_policies:
                st.markdown(f"- {policy}")
        else:
            st.info("No inline policies found.")
        
        # Display resource-based policy
        st.markdown("#### Resource-Based Policy")
        if function_policy:
            st.json(function_policy)
        else:
            st.info("No resource-based policy found.")
    
    # Test function tab
    with tabs[3]:
        st.markdown("### Test Function")
        
        # Create tabs for Quick Test and Saved Test Events
        test_tab1, test_tab2 = st.tabs(["Quick Test", "Saved Test Events"])
        
        # Quick Test tab
        with test_tab1:
            st.markdown("#### Test Payload (JSON)")
            
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
                "Template",
                template_options,
                key=f"event_template_{function_name}"
            )
            
            # Generate template JSON based on selection
            template_json = get_event_template(selected_template)
            
            # Test payload input
            default_payload = json.dumps(template_json, indent=2)
            test_payload = st.text_area("Enter test payload", default_payload, height=200)
            
            # Validate JSON
            valid_json = True
            try:
                if test_payload:
                    json.loads(test_payload)
            except json.JSONDecodeError:
                st.error("Invalid JSON payload")
                valid_json = False
            
            # Invocation type
            invocation_type = st.radio(
                "Invocation Type",
                ["RequestResponse", "Event", "DryRun"],
                horizontal=True,
                help="RequestResponse: Synchronous invocation, Event: Asynchronous invocation, DryRun: Validate parameters without executing"
            )
            
            # Invoke function button
            if st.button("Invoke Function", key=f"invoke_{function_name}") and valid_json:
                with st.spinner(f"Invoking {function_name}..."):
                    try:
                        payload = json.loads(test_payload) if test_payload else {}
                        result = lambda_client.invoke_function(
                            function_name=function_name,
                            payload=payload,
                            invocation_type=invocation_type,
                            fetch_logs=True
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
                        
                        # Create tabs for response and logs
                        response_tab, logs_tab = st.tabs(["Response", "Logs"])
                        
                        # Response tab
                        with response_tab:
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
                        with logs_tab:
                            # Display logs from the response if available
                            if 'LogResult' in result:
                                st.markdown("#### Execution Logs")
                                st.code(result['LogResult'], language="text")
                            
                            # Display CloudWatch logs if available
                            if 'CloudWatchLogs' in result and result['CloudWatchLogs']:
                                st.markdown("#### CloudWatch Logs")
                                
                                # Create a formatted log output
                                log_output = ""
                                for log in result['CloudWatchLogs']:
                                    timestamp = datetime.datetime.fromtimestamp(log.get('timestamp', 0)/1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                                    message = log.get('message', '')
                                    log_output += f"{timestamp} - {message}\n"
                                
                                st.code(log_output, language="text")
                            
                            # If no logs are available
                            if 'LogResult' not in result and 'CloudWatchLogs' not in result:
                                st.info("No logs available. This could be due to the invocation type or log retention settings.")
                        
                    except Exception as e:
                        st.error(f"Error invoking function: {str(e)}")
        
        # Saved Test Events tab
        with test_tab2:
            st.markdown("#### Saved Test Events")
            st.info("An event is an input to your Lambda function. You can create up to 10 test events per function. Saved events are stored in Lambda and are preserved if you switch browsers or machines.")
            
            # Initialize session state for test events if not exists
            if 'test_events' not in st.session_state:
                st.session_state.test_events = {}
            
            if function_name not in st.session_state.test_events:
                st.session_state.test_events[function_name] = []
            
            # Create new test event
            st.subheader("Create Test Event")
            
            # Test event name
            event_name = st.text_input("Event Name", key=f"new_event_name_{function_name}")
            
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
                key=f"saved_event_template_{function_name}"
            )
            
            # Generate template JSON based on selection
            template_json = get_event_template(selected_template)
            
            # JSON editor for event payload
            event_json = st.text_area(
                "Event JSON",
                value=json.dumps(template_json, indent=2),
                height=200,
                key=f"event_json_{function_name}"
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
                if st.button("Save Test Event", key=f"save_event_{function_name}", disabled=not event_name or not json_valid):
                    # Check if we already have 10 events
                    if len(st.session_state.test_events[function_name]) >= 10:
                        st.error("You can create up to 10 test events per function. Please delete some events first.")
                    else:
                        # Add new event
                        import uuid
                        import time
                        new_event = {
                            "id": str(uuid.uuid4()),
                            "name": event_name,
                            "json": event_json,
                            "created_at": time.time()
                        }
                        
                        st.session_state.test_events[function_name].append(new_event)
                        st.success(f"Test event '{event_name}' saved successfully!")
            
            with col2:
                if st.button("Test Function", key=f"test_saved_{function_name}", disabled=not json_valid):
                    with st.spinner("Invoking Lambda function..."):
                        try:
                            # Invoke Lambda function
                            response = lambda_client.invoke_function(
                                function_name=function_name,
                                payload=json.loads(event_json)
                            )
                            
                            # Display result
                            st.markdown("#### Invocation Result")
                            
                            # Status code
                            status_code = response.get('StatusCode', 0)
                            if status_code >= 200 and status_code < 300:
                                st.success(f"Status Code: {status_code}")
                            else:
                                st.error(f"Status Code: {status_code}")
                            
                            # Check for function error
                            if 'FunctionError' in response:
                                st.error(f"Function Error: {response['FunctionError']}")
                            
                            # Create tabs for response and logs
                            response_tab, logs_tab = st.tabs(["Response", "Logs"])
                            
                            # Response tab
                            with response_tab:
                                if 'Response' in response:
                                    if isinstance(response['Response'], dict) or isinstance(response['Response'], list):
                                        st.json(response['Response'])
                                    else:
                                        st.code(response['Response'], language="text")
                                else:
                                    st.info("No response data available.")
                            
                            # Logs tab
                            with logs_tab:
                                # Display logs from the response if available
                                if 'LogResult' in response:
                                    st.markdown("#### Execution Logs")
                                    st.code(response['LogResult'], language="text")
                                else:
                                    st.info("No logs available.")
                        except Exception as e:
                            st.error(f"Error invoking function: {str(e)}")
            
            # Display saved test events
            if st.session_state.test_events[function_name]:
                st.subheader("Your Saved Test Events")
                
                # Display events in a table
                for i, event in enumerate(st.session_state.test_events[function_name]):
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
                                            function_name=function_name,
                                            payload=json.loads(event['json'])
                                        )
                                        
                                        # Display result
                                        st.markdown("#### Invocation Result")
                                        
                                        # Status code
                                        status_code = response.get('StatusCode', 0)
                                        if status_code >= 200 and status_code < 300:
                                            st.success(f"Status Code: {status_code}")
                                        else:
                                            st.error(f"Status Code: {status_code}")
                                        
                                        # Check for function error
                                        if 'FunctionError' in response:
                                            st.error(f"Function Error: {response['FunctionError']}")
                                        
                                        # Create tabs for response and logs
                                        response_tab, logs_tab = st.tabs(["Response", "Logs"])
                                        
                                        # Response tab
                                        with response_tab:
                                            if 'Response' in response:
                                                if isinstance(response['Response'], dict) or isinstance(response['Response'], list):
                                                    st.json(response['Response'])
                                                else:
                                                    st.code(response['Response'], language="text")
                                            else:
                                                st.info("No response data available.")
                                        
                                        # Logs tab
                                        with logs_tab:
                                            # Display logs from the response if available
                                            if 'LogResult' in response:
                                                st.markdown("#### Execution Logs")
                                                st.code(response['LogResult'], language="text")
                                            else:
                                                st.info("No logs available.")
                                    except Exception as e:
                                        st.error(f"Error invoking function: {str(e)}")
                        
                        with col3:
                            if st.button("Delete", key=f"delete_{event['id']}"):
                                # Remove event
                                st.session_state.test_events[function_name] = [
                                    e for e in st.session_state.test_events[function_name] 
                                    if e['id'] != event['id']
                                ]
                                st.experimental_rerun()
                        
                        # Show event JSON in expander
                        with st.expander("Event JSON", expanded=False):
                            st.code(event['json'], language="json")
                        
                        st.markdown("---")
            else:
                st.info("No saved test events for this function yet.")


def render_lambda_metrics(lambda_client: Optional[LambdaClient] = None) -> None:
    """
    Render Lambda metrics dashboard.
    
    Args:
        lambda_client: Optional LambdaClient instance
    """
    st.markdown("""
    <div class="stcard">
        <h3>📊 Lambda Metrics</h3>
    """, unsafe_allow_html=True)
    
    # Check if user has explicitly connected to AWS
    if 'aws_connected' not in st.session_state or not st.session_state.aws_connected:
        st.warning("Please click 'Connect to AWS' in the sidebar to view Lambda metrics.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    if not lambda_client or not lambda_client.is_authenticated():
        st.warning("AWS connection failed. Please check your credentials and try connecting again.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Fetch Lambda functions
    with st.spinner("Fetching Lambda functions..."):
        functions = lambda_client.list_functions()
    
    if not functions:
        st.info("No Lambda functions found in the current region.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Function selection
    function_names = [func.get('FunctionName', '') for func in functions]
    selected_function = st.selectbox("Select a function", function_names)
    
    if selected_function:
        # Fetch metrics for the selected function
        with st.spinner(f"Fetching metrics for {selected_function}..."):
            metrics = lambda_client.get_function_metrics(selected_function)
        
        if not metrics:
            st.info(f"No metrics available for {selected_function}.")
            st.markdown("</div>", unsafe_allow_html=True)
            return
        
        # Display metrics
        col1, col2 = st.columns(2)
        
        # Invocations chart
        with col1:
            invocations = metrics.get('invocations', [])
            if invocations:
                # Create DataFrame for invocations
                invocations_df = pd.DataFrame([
                    {
                        'Timestamp': datapoint.get('Timestamp'),
                        'Invocations': datapoint.get('Sum', 0)
                    }
                    for datapoint in invocations
                ])
                
                if not invocations_df.empty:
                    # Sort by timestamp
                    invocations_df = invocations_df.sort_values('Timestamp')
                    
                    # Create chart
                    fig = px.line(
                        invocations_df,
                        x='Timestamp',
                        y='Invocations',
                        title=f"Invocations - {selected_function}",
                        template='plotly_white'
                    )
                    
                    fig.update_traces(
                        line=dict(color='#007bff', width=3),
                        mode='lines+markers',
                        marker=dict(size=8, color='#007bff')
                    )
                    
                    fig.update_layout(
                        xaxis=dict(title='Time'),
                        yaxis=dict(title='Invocations'),
                        margin=dict(l=20, r=20, t=40, b=20),
                        plot_bgcolor='rgba(255, 255, 255, 0.95)',
                        paper_bgcolor='rgba(255, 255, 255, 0.95)'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No invocation data available.")
            else:
                st.info("No invocation metrics available.")
        
        # Errors chart
        with col2:
            errors = metrics.get('errors', [])
            if errors:
                # Create DataFrame for errors
                errors_df = pd.DataFrame([
                    {
                        'Timestamp': datapoint.get('Timestamp'),
                        'Errors': datapoint.get('Sum', 0)
                    }
                    for datapoint in errors
                ])
                
                if not errors_df.empty:
                    # Sort by timestamp
                    errors_df = errors_df.sort_values('Timestamp')
                    
                    # Create chart
                    fig = px.line(
                        errors_df,
                        x='Timestamp',
                        y='Errors',
                        title=f"Errors - {selected_function}",
                        template='plotly_white'
                    )
                    
                    fig.update_traces(
                        line=dict(color='#dc3545', width=3),
                        mode='lines+markers',
                        marker=dict(size=8, color='#dc3545')
                    )
                    
                    fig.update_layout(
                        xaxis=dict(title='Time'),
                        yaxis=dict(title='Errors'),
                        margin=dict(l=20, r=20, t=40, b=20),
                        plot_bgcolor='rgba(255, 255, 255, 0.95)',
                        paper_bgcolor='rgba(255, 255, 255, 0.95)'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No error data available.")
            else:
                st.info("No error metrics available.")
        
        # Duration chart
        duration = metrics.get('duration', [])
        if duration:
            # Create DataFrame for duration
            duration_df = pd.DataFrame([
                {
                    'Timestamp': datapoint.get('Timestamp'),
                    'Average Duration': datapoint.get('Average', 0),
                    'Maximum Duration': datapoint.get('Maximum', 0)
                }
                for datapoint in duration
            ])
            
            if not duration_df.empty:
                # Sort by timestamp
                duration_df = duration_df.sort_values('Timestamp')
                
                # Create chart
                fig = go.Figure()
                
                # Add average duration line
                fig.add_trace(go.Scatter(
                    x=duration_df['Timestamp'],
                    y=duration_df['Average Duration'],
                    name='Average Duration',
                    line=dict(color='#fd7e14', width=3),
                    mode='lines+markers',
                    marker=dict(size=8, color='#fd7e14')
                ))
                
                # Add maximum duration line
                fig.add_trace(go.Scatter(
                    x=duration_df['Timestamp'],
                    y=duration_df['Maximum Duration'],
                    name='Maximum Duration',
                    line=dict(color='#dc3545', width=3, dash='dash'),
                    mode='lines+markers',
                    marker=dict(size=8, color='#dc3545')
                ))
                
                fig.update_layout(
                    title=f"Duration - {selected_function}",
                    xaxis=dict(title='Time'),
                    yaxis=dict(title='Duration (ms)'),
                    margin=dict(l=20, r=20, t=40, b=20),
                    plot_bgcolor='rgba(255, 255, 255, 0.95)',
                    paper_bgcolor='rgba(255, 255, 255, 0.95)',
                    legend=dict(
                        orientation='h',
                        yanchor='bottom',
                        y=1.02,
                        xanchor='right',
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No duration data available.")
        else:
            st.info("No duration metrics available.")
    
    st.markdown("</div>", unsafe_allow_html=True)
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

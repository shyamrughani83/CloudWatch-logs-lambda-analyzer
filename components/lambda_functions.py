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
    
    # Display the table
    if not filtered_df.empty:
        st.dataframe(
            filtered_df[['Name', 'Runtime', 'Memory (MB)', 'Timeout (s)', 'Last Modified']],
            use_container_width=True
        )
        
        # Function details and management
        st.subheader("Function Details")
        
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
        
        # Test payload input
        st.markdown("#### Test Payload (JSON)")
        default_payload = "{}"
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
        if st.button("Invoke Function") and valid_json:
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

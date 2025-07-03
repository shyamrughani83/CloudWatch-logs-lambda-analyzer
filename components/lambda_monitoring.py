"""
Lambda Monitoring component for CloudWatch Logs Analyzer.
Displays CloudWatch metrics and logs for Lambda functions.
"""

import streamlit as st
import pandas as pd
import boto3
import datetime
import time
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional
from utils.lambda_client import LambdaClient
from utils.logger import get_logger

# Initialize logger
logger = get_logger("lambda_monitoring")

def render_lambda_monitoring(lambda_client: Optional[LambdaClient] = None) -> None:
    """
    Render Lambda monitoring interface with CloudWatch metrics and logs.
    
    Args:
        lambda_client: Optional LambdaClient instance
    """
    st.markdown("""
    <div class="stcard">
        <h3>📊 Lambda Monitoring</h3>
    """, unsafe_allow_html=True)
    
    # Check if user has explicitly connected to AWS
    if 'aws_connected' not in st.session_state or not st.session_state.aws_connected:
        st.warning("Please click 'Connect to AWS' in the sidebar to view Lambda monitoring.")
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
    selected_function = st.selectbox(
        "Select a Lambda function to monitor",
        function_names,
        key="monitoring_function_selector"
    )
    
    if not selected_function:
        st.info("Please select a Lambda function to view monitoring data.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Time range selection
    st.subheader("Select Time Range")
    
    time_range_options = [
        "Last 30 minutes",
        "Last hour",
        "Last 3 hours",
        "Last 24 hours",
        "Last 7 days",
        "Custom"
    ]
    
    time_range = st.selectbox(
        "Time range",
        time_range_options,
        index=2  # Default to "Last 3 hours"
    )
    
    # Calculate start and end times based on selection
    end_time = datetime.datetime.utcnow()
    
    if time_range == "Last 30 minutes":
        start_time = end_time - datetime.timedelta(minutes=30)
        period = 60  # 1-minute data points
    elif time_range == "Last hour":
        start_time = end_time - datetime.timedelta(hours=1)
        period = 60  # 1-minute data points
    elif time_range == "Last 3 hours":
        start_time = end_time - datetime.timedelta(hours=3)
        period = 300  # 5-minute data points
    elif time_range == "Last 24 hours":
        start_time = end_time - datetime.timedelta(hours=24)
        period = 3600  # 1-hour data points
    elif time_range == "Last 7 days":
        start_time = end_time - datetime.timedelta(days=7)
        period = 86400  # 1-day data points
    else:  # Custom
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input(
                "Start date",
                value=end_time.date() - datetime.timedelta(days=1)
            )
        with col2:
            end_date = st.date_input(
                "End date",
                value=end_time.date()
            )
        
        start_time = datetime.datetime.combine(start_date, datetime.time.min)
        end_time = datetime.datetime.combine(end_date, datetime.time.max)
        
        # Calculate appropriate period based on time range
        time_diff = end_time - start_time
        if time_diff.total_seconds() <= 3600:  # 1 hour or less
            period = 60  # 1-minute data points
        elif time_diff.total_seconds() <= 86400:  # 1 day or less
            period = 300  # 5-minute data points
        elif time_diff.total_seconds() <= 604800:  # 7 days or less
            period = 3600  # 1-hour data points
        else:
            period = 86400  # 1-day data points
    
    # Create tabs for Metrics and Logs
    metrics_tab, logs_tab = st.tabs(["📈 Metrics", "📋 Logs"])
    
    # Metrics tab
    with metrics_tab:
        st.subheader(f"CloudWatch Metrics for {selected_function}")
        
        # Fetch metrics
        with st.spinner("Fetching CloudWatch metrics..."):
            try:
                # Create CloudWatch client
                session = boto3.Session(
                    region_name=lambda_client.region,
                    profile_name=lambda_client.profile
                )
                cloudwatch = session.client('cloudwatch')
                
                # Define metrics to fetch
                metrics = [
                    {"name": "Invocations", "stat": "Sum", "unit": "Count"},
                    {"name": "Errors", "stat": "Sum", "unit": "Count"},
                    {"name": "Duration", "stat": "Average", "unit": "Milliseconds"},
                    {"name": "Throttles", "stat": "Sum", "unit": "Count"},
                    {"name": "ConcurrentExecutions", "stat": "Maximum", "unit": "Count"},
                    {"name": "DeadLetterErrors", "stat": "Sum", "unit": "Count"}
                ]
                
                # Create a grid layout for metrics
                col1, col2 = st.columns(2)
                
                # Fetch and display each metric
                for i, metric in enumerate(metrics):
                    # Get metric data
                    response = cloudwatch.get_metric_statistics(
                        Namespace='AWS/Lambda',
                        MetricName=metric["name"],
                        Dimensions=[
                            {
                                'Name': 'FunctionName',
                                'Value': selected_function
                            }
                        ],
                        StartTime=start_time,
                        EndTime=end_time,
                        Period=period,
                        Statistics=[metric["stat"]]
                    )
                    
                    # Process data points
                    datapoints = response.get('Datapoints', [])
                    
                    # Choose column based on index
                    col = col1 if i % 2 == 0 else col2
                    
                    if datapoints:
                        # Sort datapoints by timestamp
                        datapoints.sort(key=lambda x: x['Timestamp'])
                        
                        # Create DataFrame for plotting
                        df = pd.DataFrame([
                            {
                                'Timestamp': dp['Timestamp'],
                                'Value': dp.get(metric["stat"], 0)
                            }
                            for dp in datapoints
                        ])
                        
                        # Calculate summary statistics
                        if metric["stat"] == "Sum":
                            total = sum(dp.get(metric["stat"], 0) for dp in datapoints)
                            summary = f"Total: {total:,.0f} {metric['unit']}"
                        elif metric["stat"] == "Average":
                            values = [dp.get(metric["stat"], 0) for dp in datapoints if dp.get(metric["stat"], 0) > 0]
                            avg = sum(values) / len(values) if values else 0
                            summary = f"Average: {avg:,.2f} {metric['unit']}"
                        elif metric["stat"] == "Maximum":
                            max_val = max((dp.get(metric["stat"], 0) for dp in datapoints), default=0)
                            summary = f"Maximum: {max_val:,.0f} {metric['unit']}"
                        
                        # Create plot
                        fig = px.line(
                            df,
                            x='Timestamp',
                            y='Value',
                            title=f"{metric['name']} ({summary})"
                        )
                        
                        # Customize plot
                        fig.update_layout(
                            xaxis_title="Time",
                            yaxis_title=f"{metric['name']} ({metric['unit']})",
                            height=300,
                            margin=dict(l=10, r=10, t=40, b=10)
                        )
                        
                        # Display plot
                        col.plotly_chart(fig, use_container_width=True)
                    else:
                        col.info(f"No {metric['name']} data available for the selected time range.")
                
                # Create a summary card with key metrics
                st.subheader("Function Summary")
                
                # Get summary metrics
                invocations = sum(dp.get('Sum', 0) for dp in cloudwatch.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Invocations',
                    Dimensions=[{'Name': 'FunctionName', 'Value': selected_function}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=int((end_time - start_time).total_seconds()),
                    Statistics=['Sum']
                ).get('Datapoints', []))
                
                errors = sum(dp.get('Sum', 0) for dp in cloudwatch.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Errors',
                    Dimensions=[{'Name': 'FunctionName', 'Value': selected_function}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=int((end_time - start_time).total_seconds()),
                    Statistics=['Sum']
                ).get('Datapoints', []))
                
                duration_data = cloudwatch.get_metric_statistics(
                    Namespace='AWS/Lambda',
                    MetricName='Duration',
                    Dimensions=[{'Name': 'FunctionName', 'Value': selected_function}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=int((end_time - start_time).total_seconds()),
                    Statistics=['Average', 'Maximum']
                ).get('Datapoints', [])
                
                avg_duration = sum(dp.get('Average', 0) for dp in duration_data) / len(duration_data) if duration_data else 0
                max_duration = max((dp.get('Maximum', 0) for dp in duration_data), default=0)
                
                # Calculate error rate
                error_rate = (errors / invocations * 100) if invocations > 0 else 0
                
                # Display summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                col1.metric(
                    "Total Invocations",
                    f"{invocations:,.0f}"
                )
                
                col2.metric(
                    "Error Rate",
                    f"{error_rate:.2f}%"
                )
                
                col3.metric(
                    "Avg Duration",
                    f"{avg_duration:.2f} ms"
                )
                
                col4.metric(
                    "Max Duration",
                    f"{max_duration:.2f} ms"
                )
                
                # Get function configuration for context
                function_config = lambda_client.get_function(selected_function).get('Configuration', {})
                
                # Display function configuration
                st.subheader("Function Configuration")
                
                col1, col2, col3 = st.columns(3)
                
                col1.metric(
                    "Memory Size",
                    f"{function_config.get('MemorySize', 0)} MB"
                )
                
                col2.metric(
                    "Timeout",
                    f"{function_config.get('Timeout', 0)} sec"
                )
                
                col3.metric(
                    "Runtime",
                    function_config.get('Runtime', 'N/A')
                )
                
                # Memory utilization analysis
                st.subheader("Memory Utilization Analysis")
                
                # Get memory utilization if available
                memory_size = function_config.get('MemorySize', 128)
                
                # Create a placeholder for memory utilization
                # Note: AWS doesn't provide direct memory utilization metrics
                # This would typically require CloudWatch Logs Insights queries
                st.info(
                    "Memory utilization data requires CloudWatch Logs Insights analysis. "
                    "Consider using the Log Explorer to analyze memory usage patterns."
                )
                
                # Provide optimization recommendations
                if avg_duration < 100 and memory_size > 128:
                    st.success(
                        f"💡 Optimization opportunity: Function has low average duration ({avg_duration:.2f} ms). "
                        f"Consider reducing memory allocation from {memory_size} MB to save costs."
                    )
                elif max_duration > (function_config.get('Timeout', 3) * 1000 * 0.8):
                    st.warning(
                        f"⚠️ Risk alert: Maximum duration ({max_duration:.2f} ms) is approaching the timeout limit "
                        f"({function_config.get('Timeout', 3) * 1000} ms). Consider increasing the timeout or optimizing the function."
                    )
                
            except Exception as e:
                st.error(f"Error fetching CloudWatch metrics: {str(e)}")
    
    # Logs tab
    with logs_tab:
        st.subheader(f"CloudWatch Logs for {selected_function}")
        
        # Fetch logs
        with st.spinner("Fetching CloudWatch logs..."):
            try:
                # Create CloudWatch Logs client
                session = boto3.Session(
                    region_name=lambda_client.region,
                    profile_name=lambda_client.profile
                )
                logs_client = session.client('logs')
                
                # Get log group name for the function
                log_group_name = f"/aws/lambda/{selected_function}"
                
                # Check if log group exists
                try:
                    logs_client.describe_log_groups(logGroupNamePrefix=log_group_name)
                except Exception:
                    st.warning(f"No log group found for {selected_function}. The function may not have been invoked yet.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return
                
                # Get log streams
                log_streams_response = logs_client.describe_log_streams(
                    logGroupName=log_group_name,
                    orderBy='LastEventTime',
                    descending=True,
                    limit=10
                )
                
                log_streams = log_streams_response.get('logStreams', [])
                
                if not log_streams:
                    st.info(f"No log streams found for {selected_function}.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return
                
                # Create a selectbox for log streams
                stream_options = [
                    {
                        'name': stream.get('logStreamName', ''),
                        'last_event': stream.get('lastEventTimestamp', 0)
                    }
                    for stream in log_streams
                ]
                
                # Format stream options for display
                stream_display_options = [
                    f"{stream['name']} (Last event: {datetime.datetime.fromtimestamp(stream['last_event']/1000).strftime('%Y-%m-%d %H:%M:%S') if stream['last_event'] else 'N/A'})"
                    for stream in stream_options
                ]
                
                selected_stream_index = st.selectbox(
                    "Select a log stream",
                    range(len(stream_display_options)),
                    format_func=lambda i: stream_display_options[i]
                )
                
                selected_stream = stream_options[selected_stream_index]['name']
                
                # Get log events
                log_events_response = logs_client.get_log_events(
                    logGroupName=log_group_name,
                    logStreamName=selected_stream,
                    startTime=int(start_time.timestamp() * 1000),
                    endTime=int(end_time.timestamp() * 1000),
                    limit=1000
                )
                
                log_events = log_events_response.get('events', [])
                
                if not log_events:
                    st.info(f"No log events found in the selected time range for stream {selected_stream}.")
                    st.markdown("</div>", unsafe_allow_html=True)
                    return
                
                # Display log events
                st.subheader(f"Log Events ({len(log_events)} events)")
                
                # Add search filter
                search_term = st.text_input("Filter logs (case-insensitive)", "")
                
                # Filter logs if search term is provided
                if search_term:
                    filtered_events = [
                        event for event in log_events
                        if search_term.lower() in event.get('message', '').lower()
                    ]
                    
                    if not filtered_events:
                        st.info(f"No log events matching '{search_term}'.")
                        st.markdown("</div>", unsafe_allow_html=True)
                        return
                    
                    display_events = filtered_events
                    st.info(f"Showing {len(filtered_events)} events matching '{search_term}'.")
                else:
                    display_events = log_events
                
                # Create a container for log events with scrolling
                log_container = st.container()
                
                # Display log events in the container
                with log_container:
                    for event in display_events:
                        timestamp = datetime.datetime.fromtimestamp(event.get('timestamp', 0)/1000)
                        message = event.get('message', '')
                        
                        # Format the log entry
                        st.text(f"{timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]} - {message}")
                
                # Add export option
                if st.button("Export Logs to CSV"):
                    # Create DataFrame from log events
                    logs_df = pd.DataFrame([
                        {
                            'Timestamp': datetime.datetime.fromtimestamp(event.get('timestamp', 0)/1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                            'Message': event.get('message', '')
                        }
                        for event in display_events
                    ])
                    
                    # Convert DataFrame to CSV
                    csv = logs_df.to_csv(index=False)
                    
                    # Create download link
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"{selected_function}_logs_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                # Add log insights query option
                st.subheader("CloudWatch Logs Insights")
                
                # Predefined queries
                predefined_queries = {
                    "Error Analysis": f"fields @timestamp, @message\n| filter @message like /ERROR|Error|error|Exception|exception/\n| sort @timestamp desc\n| limit 100",
                    "Cold Start Analysis": f"fields @timestamp, @message\n| filter @message like /Init Duration/\n| sort @timestamp desc\n| limit 100",
                    "Duration Analysis": f"filter @type = \"REPORT\"\n| stats avg(@duration), max(@duration), min(@duration) by bin(5m)",
                    "Memory Usage": f"filter @type = \"REPORT\"\n| stats avg(@maxMemoryUsed / 1000000) as avgMemoryUsedMB, max(@maxMemoryUsed / 1000000) as maxMemoryUsedMB by bin(5m)"
                }
                
                # Query selection
                selected_query_name = st.selectbox(
                    "Select a predefined query",
                    list(predefined_queries.keys())
                )
                
                # Display and allow editing of the selected query
                query = st.text_area(
                    "CloudWatch Logs Insights Query",
                    value=predefined_queries[selected_query_name],
                    height=150
                )
                
                # Add a note about running the query
                st.info(
                    "To run this query, copy it and navigate to the CloudWatch Logs Insights console. "
                    "Select the log group `/aws/lambda/" + selected_function + "` and paste the query."
                )
                
                # Add a direct link to CloudWatch Logs Insights
                region = lambda_client.region
                logs_insights_url = f"https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}#logsV2:logs-insights"
                
                st.markdown(f"[Open CloudWatch Logs Insights Console]({logs_insights_url})")
                
            except Exception as e:
                st.error(f"Error fetching CloudWatch logs: {str(e)}")
    
    st.markdown("</div>", unsafe_allow_html=True)

"""
Log Groups component for CloudWatch Logs Analyzer.
Displays and manages CloudWatch Log Groups with enhanced UI.
"""

import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional
from utils.aws_client import CloudWatchLogsClient
from utils.logger import get_logger

# Initialize logger
logger = get_logger("log_groups")

def render_log_groups(aws_client: Optional[CloudWatchLogsClient] = None) -> None:
    """
    Render Log Groups management interface with enhanced UI.
    
    Args:
        aws_client: Optional CloudWatchLogsClient instance
    """
    st.markdown("""
    <div class="stcard">
        <h3>📚 CloudWatch Log Groups</h3>
    """, unsafe_allow_html=True)
    
    # Check if user has explicitly connected to AWS
    if 'aws_connected' not in st.session_state or not st.session_state.aws_connected:
        st.warning("Please click 'Connect to AWS' in the sidebar to view and manage Log Groups.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    if not aws_client or not aws_client.is_authenticated():
        st.warning("AWS connection failed. Please check your credentials and try connecting again.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Fetch Log Groups
    with st.spinner("Fetching Log Groups..."):
        log_groups = aws_client.get_log_groups()
    
    if not log_groups:
        st.info("No Log Groups found in the current region.")
        st.markdown("</div>", unsafe_allow_html=True)
        return
    
    # Create a DataFrame for the log groups
    log_groups_df = pd.DataFrame([
        {
            'Name': lg.get('logGroupName', ''),
            'Creation Time': datetime.datetime.fromtimestamp(lg.get('creationTime', 0)/1000).strftime('%Y-%m-%d %H:%M:%S'),
            'Retention (days)': lg.get('retentionInDays', 'Never Expire'),
            'Stored Bytes': lg.get('storedBytes', 0),
            'ARN': lg.get('arn', '')
        }
        for lg in log_groups
    ])
    
    # Display log groups in a searchable table
    st.subheader("Available Log Groups")
    
    # Add search box with improved styling
    col1, col2 = st.columns([3, 1])
    with col1:
        search_term = st.text_input(
            "Search log groups",
            "",
            placeholder="Enter log group name or pattern",
            help="Filter log groups by name"
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort by",
            ["Name", "Creation Time", "Stored Bytes", "Retention (days)"],
            help="Sort log groups by selected column"
        )
    
    # Filter log groups based on search term
    if search_term:
        filtered_df = log_groups_df[log_groups_df['Name'].str.contains(search_term, case=False)]
    else:
        filtered_df = log_groups_df
    
    # Sort the dataframe
    if sort_by == "Stored Bytes":
        filtered_df = filtered_df.sort_values(by=sort_by, ascending=False)
    else:
        filtered_df = filtered_df.sort_values(by=sort_by)
    
    # Display the table with improved styling
    if not filtered_df.empty:
        # Format stored bytes to be more readable
        filtered_df['Stored Bytes'] = filtered_df['Stored Bytes'].apply(
            lambda x: f"{x/1024/1024:.2f} MB" if x >= 1024*1024 else f"{x/1024:.2f} KB" if x >= 1024 else f"{x} B"
        )
        
        st.dataframe(
            filtered_df[['Name', 'Creation Time', 'Retention (days)', 'Stored Bytes']],
            use_container_width=True,
            height=300
        )
        
        # Log group details and management
        st.subheader("Log Group Details")
        
        # Select a log group to view details with improved UI
        selected_log_group = st.selectbox(
            "Select a log group to view details",
            filtered_df['Name'].tolist(),
            format_func=lambda x: x.split('/')[-1] if '/' in x else x,
            help="Select a log group to view detailed information and logs"
        )
        
        if selected_log_group:
            display_log_group_details(aws_client, selected_log_group)
    else:
        st.info("No log groups match your search criteria.")
    
    st.markdown("</div>", unsafe_allow_html=True)

def display_log_group_details(aws_client: CloudWatchLogsClient, log_group_name: str) -> None:
    """
    Display details for a selected CloudWatch Log Group.
    
    Args:
        aws_client: CloudWatchLogsClient instance
        log_group_name: Name of the Log Group
    """
    # Create tabs for different log group views
    tabs = st.tabs(["Overview", "Log Streams", "Metrics", "Query Logs"])
    
    # Get log group details
    with st.spinner(f"Fetching details for {log_group_name}..."):
        log_group_details = aws_client.describe_log_group(log_group_name)
    
    if not log_group_details:
        st.error(f"Failed to fetch details for {log_group_name}")
        return
    
    # Extract details
    creation_time = datetime.datetime.fromtimestamp(log_group_details.get('creationTime', 0)/1000)
    retention_days = log_group_details.get('retentionInDays', 'Never Expire')
    stored_bytes = log_group_details.get('storedBytes', 0)
    
    # Format stored bytes to be more readable
    if stored_bytes >= 1024*1024*1024:
        stored_bytes_formatted = f"{stored_bytes/1024/1024/1024:.2f} GB"
    elif stored_bytes >= 1024*1024:
        stored_bytes_formatted = f"{stored_bytes/1024/1024:.2f} MB"
    elif stored_bytes >= 1024:
        stored_bytes_formatted = f"{stored_bytes/1024:.2f} KB"
    else:
        stored_bytes_formatted = f"{stored_bytes} B"
    
    # Overview tab
    with tabs[0]:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">📚</div>
                <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 500;">Log Group Name</div>
                <div style="font-size: 1.4rem; font-weight: 700; margin-bottom: 0.25rem; color: #007bff;">{log_group_name.split('/')[-1]}</div>
                <div style="font-size: 0.8rem; color: #6c757d;">Created: {creation_time.strftime('%Y-%m-%d %H:%M:%S')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">💾</div>
                <div style="font-size: 0.9rem; color: #6c757d; margin-bottom: 0.5rem; font-weight: 500;">Storage</div>
                <div style="font-size: 1.4rem; font-weight: 700; margin-bottom: 0.25rem; color: #007bff;">{stored_bytes_formatted}</div>
                <div style="font-size: 0.8rem; color: #6c757d;">Retention: {retention_days} days</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Log Group ARN and other details
        st.markdown("### Log Group Details")
        st.code(log_group_details.get('arn', 'N/A'), language="text")
        
        # Retention settings
        st.markdown("### Retention Settings")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            current_retention = retention_days if retention_days != 'Never Expire' else 0
            new_retention = st.select_slider(
                "Retention Period (days)",
                options=[0, 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653],
                value=current_retention if isinstance(current_retention, int) else 0,
                help="0 means never expire"
            )
        
        with col2:
            st.write("")
            st.write("")
            if st.button("Update Retention"):
                with st.spinner("Updating retention settings..."):
                    if new_retention == 0:
                        result = aws_client.delete_retention_policy(log_group_name)
                        message = "Retention policy removed (logs will never expire)"
                    else:
                        result = aws_client.put_retention_policy(log_group_name, new_retention)
                        message = f"Retention period set to {new_retention} days"
                    
                    if result:
                        st.success(message)
                        st.experimental_rerun()
                    else:
                        st.error("Failed to update retention settings")
        
        # Recent activity
        st.markdown("### Recent Activity")
        with st.spinner("Fetching recent logs..."):
            recent_logs, _ = aws_client.get_log_events(
                log_group_name=log_group_name,
                limit=5
            )
        
        if recent_logs:
            for log in recent_logs:
                timestamp = datetime.datetime.fromtimestamp(log.get('timestamp', 0)/1000).strftime('%Y-%m-%d %H:%M:%S')
                message = log.get('message', '')
                st.markdown(f"""
                <div style="padding: 10px; border-left: 3px solid #007bff; margin-bottom: 10px; background-color: #f8f9fa; border-radius: 5px;">
                    <div style="font-size: 0.8rem; color: #6c757d;">{timestamp}</div>
                    <div style="font-family: monospace; white-space: pre-wrap;">{message}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No recent logs available.")
    
    # Log Streams tab
    with tabs[1]:
        st.markdown("### Log Streams")
        
        # Add search box for log streams
        stream_search = st.text_input(
            "Search log streams",
            "",
            placeholder="Enter stream name or pattern",
            help="Filter log streams by name"
        )
        
        # Fetch log streams
        with st.spinner("Fetching log streams..."):
            log_streams = aws_client.get_log_streams(
                log_group_name=log_group_name,
                prefix=stream_search if stream_search else None
            )
        
        if log_streams:
            # Create a DataFrame for the log streams
            streams_df = pd.DataFrame([
                {
                    'Stream Name': stream.get('logStreamName', ''),
                    'Last Event': datetime.datetime.fromtimestamp(stream.get('lastEventTimestamp', 0)/1000).strftime('%Y-%m-%d %H:%M:%S') if stream.get('lastEventTimestamp') else 'N/A',
                    'First Event': datetime.datetime.fromtimestamp(stream.get('firstEventTimestamp', 0)/1000).strftime('%Y-%m-%d %H:%M:%S') if stream.get('firstEventTimestamp') else 'N/A',
                    'Size (bytes)': stream.get('storedBytes', 0)
                }
                for stream in log_streams
            ])
            
            # Format size to be more readable
            streams_df['Size'] = streams_df['Size (bytes)'].apply(
                lambda x: f"{x/1024/1024:.2f} MB" if x >= 1024*1024 else f"{x/1024:.2f} KB" if x >= 1024 else f"{x} B"
            )
            
            # Display the table
            st.dataframe(
                streams_df[['Stream Name', 'Last Event', 'First Event', 'Size']],
                use_container_width=True,
                height=300
            )
            
            # Select a stream to view logs
            selected_stream = st.selectbox(
                "Select a stream to view logs",
                streams_df['Stream Name'].tolist(),
                help="Select a log stream to view its logs"
            )
            
            if selected_stream:
                st.markdown(f"### Logs from {selected_stream}")
                
                # Add time range selector
                col1, col2 = st.columns(2)
                with col1:
                    start_time = st.date_input(
                        "Start Date",
                        value=datetime.datetime.now() - datetime.timedelta(hours=1),
                        help="Start date for log events"
                    )
                with col2:
                    end_time = st.date_input(
                        "End Date",
                        value=datetime.datetime.now(),
                        help="End date for log events"
                    )
                
                # Convert to datetime
                start_datetime = datetime.datetime.combine(start_time, datetime.time.min)
                end_datetime = datetime.datetime.combine(end_time, datetime.time.max)
                
                # Fetch logs for the selected stream
                with st.spinner(f"Fetching logs for {selected_stream}..."):
                    logs, _ = aws_client.get_log_events(
                        log_group_name=log_group_name,
                        log_stream_name=selected_stream,
                        start_time=int(start_datetime.timestamp() * 1000),
                        end_time=int(end_datetime.timestamp() * 1000)
                    )
                
                if logs:
                    # Display logs with improved styling
                    for log in logs:
                        timestamp = datetime.datetime.fromtimestamp(log.get('timestamp', 0)/1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                        message = log.get('message', '')
                        
                        # Determine log level for color coding
                        log_level = "INFO"
                        if "ERROR" in message or "FATAL" in message:
                            log_color = "#dc3545"  # Red for errors
                            log_level = "ERROR"
                        elif "WARN" in message:
                            log_color = "#ffc107"  # Yellow for warnings
                            log_level = "WARN"
                        elif "DEBUG" in message:
                            log_color = "#6c757d"  # Gray for debug
                            log_level = "DEBUG"
                        else:
                            log_color = "#28a745"  # Green for info
                        
                        st.markdown(f"""
                        <div style="padding: 10px; border-left: 3px solid {log_color}; margin-bottom: 10px; background-color: #f8f9fa; border-radius: 5px;">
                            <div style="display: flex; justify-content: space-between;">
                                <div style="font-size: 0.8rem; color: #6c757d;">{timestamp}</div>
                                <div style="font-size: 0.8rem; color: {log_color}; font-weight: bold;">{log_level}</div>
                            </div>
                            <div style="font-family: monospace; white-space: pre-wrap;">{message}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.info("No logs found for the selected time range.")
        else:
            st.info("No log streams found.")
    
    # Metrics tab
    with tabs[2]:
        st.markdown("### Log Group Metrics")
        
        # Time range selector for metrics
        col1, col2 = st.columns(2)
        with col1:
            period = st.selectbox(
                "Time Period",
                ["Last Hour", "Last 3 Hours", "Last 24 Hours", "Last 7 Days"],
                index=1,
                help="Select time period for metrics"
            )
        
        with col2:
            granularity = st.selectbox(
                "Granularity",
                ["1 Minute", "5 Minutes", "1 Hour", "1 Day"],
                index=1,
                help="Select granularity for metrics"
            )
        
        # Convert selections to actual values
        if period == "Last Hour":
            start_time = datetime.datetime.now() - datetime.timedelta(hours=1)
        elif period == "Last 3 Hours":
            start_time = datetime.datetime.now() - datetime.timedelta(hours=3)
        elif period == "Last 24 Hours":
            start_time = datetime.datetime.now() - datetime.timedelta(days=1)
        else:  # Last 7 Days
            start_time = datetime.datetime.now() - datetime.timedelta(days=7)
        
        end_time = datetime.datetime.now()
        
        if granularity == "1 Minute":
            period_seconds = 60
        elif granularity == "5 Minutes":
            period_seconds = 300
        elif granularity == "1 Hour":
            period_seconds = 3600
        else:  # 1 Day
            period_seconds = 86400
        
        # Fetch metrics
        with st.spinner("Fetching metrics..."):
            metrics = aws_client.get_log_group_metrics(
                log_group_name=log_group_name,
                start_time=start_time,
                end_time=end_time,
                period=period_seconds
            )
        
        if metrics:
            # Create metrics charts
            col1, col2 = st.columns(2)
            
            # Incoming logs chart
            with col1:
                incoming_logs = metrics.get('IncomingLogEvents', [])
                if incoming_logs:
                    # Create DataFrame for incoming logs
                    incoming_df = pd.DataFrame([
                        {
                            'Timestamp': datapoint.get('Timestamp'),
                            'Count': datapoint.get('Sum', 0)
                        }
                        for datapoint in incoming_logs
                    ])
                    
                    if not incoming_df.empty:
                        # Sort by timestamp
                        incoming_df = incoming_df.sort_values('Timestamp')
                        
                        # Create chart
                        fig = px.line(
                            incoming_df,
                            x='Timestamp',
                            y='Count',
                            title="Incoming Log Events",
                            template='plotly_white'
                        )
                        
                        fig.update_traces(
                            line=dict(color='#007bff', width=3),
                            mode='lines+markers',
                            marker=dict(size=8, color='#007bff')
                        )
                        
                        fig.update_layout(
                            xaxis=dict(title='Time'),
                            yaxis=dict(title='Count'),
                            margin=dict(l=20, r=20, t=40, b=20),
                            plot_bgcolor='rgba(255, 255, 255, 0.95)',
                            paper_bgcolor='rgba(255, 255, 255, 0.95)'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No incoming log events data available.")
                else:
                    st.info("No incoming log events metrics available.")
            
            # Ingested bytes chart
            with col2:
                ingested_bytes = metrics.get('IncomingBytes', [])
                if ingested_bytes:
                    # Create DataFrame for ingested bytes
                    bytes_df = pd.DataFrame([
                        {
                            'Timestamp': datapoint.get('Timestamp'),
                            'Bytes': datapoint.get('Sum', 0)
                        }
                        for datapoint in ingested_bytes
                    ])
                    
                    if not bytes_df.empty:
                        # Sort by timestamp
                        bytes_df = bytes_df.sort_values('Timestamp')
                        
                        # Convert bytes to KB for better readability
                        bytes_df['KB'] = bytes_df['Bytes'] / 1024
                        
                        # Create chart
                        fig = px.line(
                            bytes_df,
                            x='Timestamp',
                            y='KB',
                            title="Ingested Data (KB)",
                            template='plotly_white'
                        )
                        
                        fig.update_traces(
                            line=dict(color='#28a745', width=3),
                            mode='lines+markers',
                            marker=dict(size=8, color='#28a745')
                        )
                        
                        fig.update_layout(
                            xaxis=dict(title='Time'),
                            yaxis=dict(title='Kilobytes'),
                            margin=dict(l=20, r=20, t=40, b=20),
                            plot_bgcolor='rgba(255, 255, 255, 0.95)',
                            paper_bgcolor='rgba(255, 255, 255, 0.95)'
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No ingested bytes data available.")
                else:
                    st.info("No ingested bytes metrics available.")
        else:
            st.info("No metrics available for this log group.")
    
    # Query Logs tab
    with tabs[3]:
        st.markdown("### Query Logs")
        
        # Add filter pattern input
        filter_pattern = st.text_input(
            "Filter Pattern",
            "",
            placeholder="e.g., ERROR or ?Exception",
            help="CloudWatch Logs filter pattern"
        )
        
        # Time range selector
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.date_input(
                "Start Date",
                value=datetime.datetime.now() - datetime.timedelta(hours=1),
                help="Start date for log events"
            )
        with col2:
            end_time = st.date_input(
                "End Date",
                value=datetime.datetime.now(),
                help="End date for log events"
            )
        
        # Convert to datetime
        start_datetime = datetime.datetime.combine(start_time, datetime.time.min)
        end_datetime = datetime.datetime.combine(end_time, datetime.time.max)
        
        # Add limit selector
        limit = st.slider(
            "Maximum Results",
            min_value=10,
            max_value=10000,
            value=100,
            step=10,
            help="Maximum number of log events to return"
        )
        
        # Query button
        if st.button("Query Logs", type="primary"):
            with st.spinner("Querying logs..."):
                logs = aws_client.filter_log_events(
                    log_group_name=log_group_name,
                    filter_pattern=filter_pattern if filter_pattern else None,
                    start_time=int(start_datetime.timestamp() * 1000),
                    end_time=int(end_datetime.timestamp() * 1000),
                    limit=limit
                )
            
            if logs:
                # Display logs with improved styling
                for log in logs:
                    timestamp = datetime.datetime.fromtimestamp(log.get('timestamp', 0)/1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    message = log.get('message', '')
                    stream_name = log.get('logStreamName', '')
                    
                    # Determine log level for color coding
                    log_level = "INFO"
                    if "ERROR" in message or "FATAL" in message:
                        log_color = "#dc3545"  # Red for errors
                        log_level = "ERROR"
                    elif "WARN" in message:
                        log_color = "#ffc107"  # Yellow for warnings
                        log_level = "WARN"
                    elif "DEBUG" in message:
                        log_color = "#6c757d"  # Gray for debug
                        log_level = "DEBUG"
                    else:
                        log_color = "#28a745"  # Green for info
                    
                    st.markdown(f"""
                    <div style="padding: 10px; border-left: 3px solid {log_color}; margin-bottom: 10px; background-color: #f8f9fa; border-radius: 5px;">
                        <div style="display: flex; justify-content: space-between;">
                            <div style="font-size: 0.8rem; color: #6c757d;">{timestamp}</div>
                            <div style="font-size: 0.8rem; color: {log_color}; font-weight: bold;">{log_level}</div>
                        </div>
                        <div style="font-size: 0.7rem; color: #6c757d; margin-bottom: 5px;">Stream: {stream_name}</div>
                        <div style="font-family: monospace; white-space: pre-wrap;">{message}</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Add export option
                if st.button("Export Results to CSV"):
                    # Create DataFrame for export
                    export_df = pd.DataFrame([
                        {
                            'Timestamp': datetime.datetime.fromtimestamp(log.get('timestamp', 0)/1000).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                            'Stream': log.get('logStreamName', ''),
                            'Message': log.get('message', '')
                        }
                        for log in logs
                    ])
                    
                    # Convert to CSV
                    csv = export_df.to_csv(index=False)
                    
                    # Create download link
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"{log_group_name.split('/')[-1]}_logs.csv",
                        mime="text/csv"
                    )
            else:
                st.info("No logs found matching your criteria.")

"""
Log Explorer component for CloudWatch Logs Analyzer.
Provides a searchable and filterable table of log entries.
"""

import streamlit as st
import pandas as pd
import re
from typing import Dict, Any, List, Optional
from utils.helpers import ensure_timezone_naive, convert_for_streamlit_display, ensure_arrow_compatible, safe_display


def render_log_explorer(log_data: pd.DataFrame) -> None:
    """
    Render the log explorer with search and filter capabilities.
    
    Args:
        log_data: DataFrame with processed log data
    """
    if log_data.empty:
        st.info("No log data available. Please fetch log data first.")
        return
    
    # Ensure datetime column is timezone-naive
    log_data = ensure_timezone_naive(log_data)
    
    st.subheader("Log Explorer")
    
    # Create filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Filter by status (error/success)
        if 'error' in log_data.columns:
            status_filter = st.selectbox(
                "Status",
                ["All", "Error", "Success"],
                index=0
            )
        else:
            status_filter = "All"
    
    with col2:
        # Filter by request ID
        request_id_filter = st.text_input("Request ID", "")
    
    with col3:
        # Filter by text in message
        text_filter = st.text_input("Text Search", "")
    
    # Apply filters
    filtered_data = log_data.copy()
    
    if status_filter == "Error" and 'error' in filtered_data.columns:
        filtered_data = filtered_data[filtered_data['error'] == True]
    elif status_filter == "Success" and 'error' in filtered_data.columns:
        filtered_data = filtered_data[filtered_data['error'] == False]
    
    if request_id_filter and 'request_id' in filtered_data.columns:
        filtered_data = filtered_data[filtered_data['request_id'].str.contains(request_id_filter, na=False)]
    
    if text_filter and 'message' in filtered_data.columns:
        filtered_data = filtered_data[filtered_data['message'].str.contains(text_filter, case=False, na=False)]
    
    # Additional filters in an expander
    with st.expander("Advanced Filters"):
        cols = st.columns(2)
        col1, col2 = cols
        
        with col1:
            # Filter by cold start
            if 'cold_start' in filtered_data.columns:
                cold_start_filter = st.selectbox(
                    "Cold Start",
                    ["All", "Yes", "No"],
                    index=0
                )
                
                if cold_start_filter == "Yes":
                    filtered_data = filtered_data[filtered_data['cold_start'] == True]
                elif cold_start_filter == "No":
                    filtered_data = filtered_data[filtered_data['cold_start'] == False]
        
        with col2:
            # Filter by duration
            if 'duration_ms' in filtered_data.columns and not filtered_data.empty:
                min_duration = filtered_data['duration_ms'].min() if not filtered_data.empty else 0
                max_duration = filtered_data['duration_ms'].max() if not filtered_data.empty else 1000
                
                # Ensure min and max values are different to avoid slider error
                if min_duration == max_duration:
                    # Add a small buffer to max_duration to make it different from min_duration
                    max_duration = min_duration + 0.01
                
                duration_range = st.slider(
                    "Duration (ms)",
                    min_value=float(min_duration),
                    max_value=float(max_duration),
                    value=(float(min_duration), float(max_duration))
                )
                
                filtered_data = filtered_data[
                    (filtered_data['duration_ms'] >= duration_range[0]) &
                    (filtered_data['duration_ms'] <= duration_range[1])
                ]
    
    # Display log count
    st.caption(f"Showing {len(filtered_data)} of {len(log_data)} log entries")
    
    # Sort options
    sort_options = {
        'Newest First': ('datetime', False),
        'Oldest First': ('datetime', True),
        'Longest Duration': ('duration_ms', False),
        'Shortest Duration': ('duration_ms', True)
    }
    
    sort_by = st.selectbox("Sort by", list(sort_options.keys()))
    sort_col, sort_asc = sort_options[sort_by]
    
    # Sort the data if the column exists
    if sort_col in filtered_data.columns:
        filtered_data = filtered_data.sort_values(sort_col, ascending=sort_asc)
    
    # Display the logs
    if not filtered_data.empty:
        # Select columns to display
        display_cols = ['datetime', 'request_id', 'duration_ms', 'memory_used_mb', 'error', 'cold_start']
        display_cols = [col for col in display_cols if col in filtered_data.columns]
        
        # Get data for display
        display_df = filtered_data[display_cols].copy()
        
        # Convert to a format safe for Streamlit display
        display_data = safe_display(display_df)
        
        # Display the table
        st.dataframe(display_data, use_container_width=True)
        
        # Log details viewer
        st.subheader("Log Details")
        
        # Select a log entry to view details
        selected_request_id = st.selectbox(
            "Select Request ID to view details",
            options=filtered_data['request_id'].unique() if 'request_id' in filtered_data.columns else []
        )
        
        if selected_request_id:
            display_log_details(log_data, selected_request_id)
    else:
        st.info("No logs match the selected filters.")


def display_log_details(log_data: pd.DataFrame, request_id: str) -> None:
    """
    Display detailed information for a specific log entry.
    
    Args:
        log_data: DataFrame with all log data
        request_id: Request ID to display details for
    """
    # Filter to only include entries for the selected request ID
    request_logs = log_data[log_data['request_id'] == request_id].sort_values('timestamp')
    
    if request_logs.empty:
        st.info(f"No logs found for request ID: {request_id}")
        return
    
    # Display request summary
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'duration_ms' in request_logs.columns:
            duration = request_logs['duration_ms'].max()
            st.metric("Duration", f"{duration:.2f} ms")
    
    with col2:
        if 'memory_used_mb' in request_logs.columns and 'memory_size_mb' in request_logs.columns:
            memory_used = request_logs['memory_used_mb'].max()
            memory_size = request_logs['memory_size_mb'].max()
            st.metric("Memory", f"{memory_used:.1f} / {memory_size:.0f} MB")
    
    with col3:
        if 'cold_start' in request_logs.columns:
            cold_start = request_logs['cold_start'].any()
            st.metric("Cold Start", "Yes" if cold_start else "No")
    
    with col4:
        if 'error' in request_logs.columns:
            error = request_logs['error'].any()
            st.metric("Status", "Error" if error else "Success", delta_color="inverse")
    
    # Display all log messages for this request
    if 'message' in request_logs.columns:
        st.markdown("### Log Messages")
        
        for _, row in request_logs.iterrows():
            message = row['message']
            timestamp = row['datetime'] if 'datetime' in row else None
            
            # Format the message
            st.markdown(
                f"""
                <div style="
                    border: 1px solid #e1e4e8;
                    border-radius: 6px;
                    padding: 0.75rem;
                    margin-bottom: 0.75rem;
                    background-color: {'#fff5f5' if row.get('error', False) else '#f8f9fa'};
                    font-family: monospace;
                    white-space: pre-wrap;
                    overflow-wrap: break-word;
                ">
                    <p style="
                        font-size: 0.8rem;
                        color: #6c757d;
                        margin-bottom: 0.25rem;
                    ">{timestamp}</p>
                    <p style="margin-bottom: 0;">{message}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    # Display additional metadata
    st.markdown("### Request Metadata")
    
    # Get all columns except message (already displayed)
    metadata_cols = [col for col in request_logs.columns if col != 'message']
    
    # Display the first row (should contain most metadata)
    if metadata_cols:
        metadata = request_logs[metadata_cols].iloc[0].to_dict()
        
        # Format as a table
        metadata_df = pd.DataFrame({
            'Key': metadata.keys(),
            'Value': metadata.values()
        })
        
        st.dataframe(metadata_df, use_container_width=True)

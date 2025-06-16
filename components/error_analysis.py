"""
Error Analysis component for CloudWatch Logs Analyzer.
Displays error patterns and distribution.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List
from utils.helpers import ensure_timezone_naive, convert_for_streamlit_display, ensure_arrow_compatible, safe_display


def render_error_analysis(error_analysis: Dict[str, Any], log_data: pd.DataFrame) -> None:
    """
    Render error analysis charts and tables.
    
    Args:
        error_analysis: Dictionary with error analysis results
        log_data: DataFrame with processed log data
    """
    if not error_analysis:
        st.info("No error analysis data available.")
        return
    
    st.subheader("Error Analysis")
    
    error_count = error_analysis.get('error_count', 0)
    error_rate = error_analysis.get('error_rate', 0)
    
    if error_count == 0:
        st.success("No errors detected in the analyzed logs.")
        return
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # Display error metrics
        st.markdown(f"### Error Metrics")
        st.metric("Error Count", error_count)
        st.metric("Error Rate", f"{error_rate * 100:.2f}%")
        
        # Display error distribution by type
        error_types = error_analysis.get('error_types', [])
        if error_types:
            st.markdown("### Error Types")
            
            # Create a pie chart of error types
            error_types_df = pd.DataFrame(error_types)
            
            fig = px.pie(
                error_types_df,
                values='count',
                names='type',
                title='Error Distribution by Type',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Display top errors
        top_errors = error_analysis.get('top_errors', [])
        if top_errors:
            st.markdown("### Top Errors")
            
            for error in top_errors[:5]:
                message = error.get('message', '')
                count = error.get('count', 0)
                percentage = error.get('percentage', 0) * 100
                
                st.markdown(
                    f"""
                    <div style="
                        border: 1px solid #e1e4e8;
                        border-radius: 6px;
                        padding: 0.75rem;
                        margin-bottom: 0.75rem;
                        background-color: #f8f9fa;
                    ">
                        <p style="
                            margin-bottom: 0.25rem;
                            font-family: monospace;
                            font-size: 0.9rem;
                            white-space: pre-wrap;
                            overflow-wrap: break-word;
                        ">{message}</p>
                        <p style="
                            font-size: 0.8rem;
                            color: #6c757d;
                            margin-bottom: 0;
                        ">Occurrences: {count} ({percentage:.1f}%)</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    # Error timeline
    if not log_data.empty and 'datetime' in log_data.columns and 'error' in log_data.columns:
        st.subheader("Error Timeline")
        
        # Create a time-series of errors
        error_data = log_data[log_data['error'] == True].copy()
        
        if not error_data.empty:
            # Ensure datetime column is timezone-naive for calculations
            error_data = ensure_timezone_naive(error_data)
            
            # Group by time intervals
            error_time_series = error_data.set_index('datetime')
            error_counts = error_time_series.resample('5min').size().reset_index(name='count')
            
            fig = px.line(
                error_counts,
                x='datetime',
                y='count',
                title='Errors Over Time',
                labels={'datetime': 'Time', 'count': 'Error Count'},
                color_discrete_sequence=['#dc3545']
            )
            
            fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Time",
                yaxis_title="Error Count"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Error details
    if not log_data.empty and 'error' in log_data.columns:
        error_data = log_data[log_data['error'] == True]
        
        if not error_data.empty:
            st.subheader("Error Details")
            
            # Allow expanding to see all errors
            with st.expander("View All Errors"):
                # Select columns to display
                display_cols = ['datetime', 'request_id', 'error_message']
                display_cols = [col for col in display_cols if col in error_data.columns]
                
                if display_cols:
                    st.dataframe(
                        error_data[display_cols].sort_values('datetime', ascending=False),
                        use_container_width=True
                    )


def render_error_correlation(log_data: pd.DataFrame) -> None:
    """
    Render error correlation analysis.
    
    Args:
        log_data: DataFrame with processed log data
    """
    if log_data.empty or 'error' not in log_data.columns:
        return
    
    st.subheader("Error Correlation Analysis")
    
    # Filter to only include entries with duration and memory info
    analysis_data = log_data.dropna(subset=['duration_ms', 'memory_used_mb'])
    
    if analysis_data.empty:
        st.info("Insufficient data for correlation analysis.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Duration vs Error correlation
        if 'duration_ms' in analysis_data.columns:
            st.markdown("### Duration vs Errors")
            
            # Create box plot of duration by error status
            fig = px.box(
                analysis_data,
                x='error',
                y='duration_ms',
                title='Duration by Error Status',
                labels={'error': 'Error', 'duration_ms': 'Duration (ms)'},
                color='error',
                color_discrete_map={True: '#dc3545', False: '#28a745'}
            )
            
            fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Error Status",
                yaxis_title="Duration (ms)"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Memory vs Error correlation
        if 'memory_used_mb' in analysis_data.columns:
            st.markdown("### Memory Usage vs Errors")
            
            # Create box plot of memory usage by error status
            fig = px.box(
                analysis_data,
                x='error',
                y='memory_used_mb',
                title='Memory Usage by Error Status',
                labels={'error': 'Error', 'memory_used_mb': 'Memory Used (MB)'},
                color='error',
                color_discrete_map={True: '#dc3545', False: '#28a745'}
            )
            
            fig.update_layout(
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis_title="Error Status",
                yaxis_title="Memory Used (MB)"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Cold Start vs Error correlation
    if 'cold_start' in analysis_data.columns:
        st.markdown("### Cold Start vs Error Correlation")
        
        # Create a contingency table
        contingency = pd.crosstab(
            analysis_data['cold_start'],
            analysis_data['error'],
            normalize='index'
        ) * 100
        
        # Create a grouped bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=['Cold Start', 'Warm Start'],
            y=[contingency.loc[True, True] if True in contingency.index and True in contingency.columns else 0,
               contingency.loc[False, True] if False in contingency.index and True in contingency.columns else 0],
            name='Error',
            marker_color='#dc3545'
        ))
        
        fig.add_trace(go.Bar(
            x=['Cold Start', 'Warm Start'],
            y=[contingency.loc[True, False] if True in contingency.index and False in contingency.columns else 0,
               contingency.loc[False, False] if False in contingency.index and False in contingency.columns else 0],
            name='Success',
            marker_color='#28a745'
        ))
        
        fig.update_layout(
            title='Error Rate by Cold Start Status',
            xaxis_title='Invocation Type',
            yaxis_title='Percentage (%)',
            barmode='stack',
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)

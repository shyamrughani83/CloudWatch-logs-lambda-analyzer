"""
Memory Chart component for CloudWatch Logs Analyzer.
Displays memory usage analysis and optimization recommendations.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, Optional
from utils.helpers import ensure_timezone_naive, convert_for_streamlit_display, ensure_arrow_compatible, safe_display


def render_memory_chart(log_data: pd.DataFrame, memory_analysis: Dict[str, Any]) -> None:
    """
    Render memory usage chart and analysis.
    
    Args:
        log_data: DataFrame with processed log data
        memory_analysis: Dictionary with memory usage analysis
    """
    if log_data.empty or 'memory_used_mb' not in log_data.columns:
        st.info("No memory usage data available.")
        return
    
    st.subheader("Memory Usage Analysis")
    
    # Filter to only include REPORT entries with memory info
    memory_data = log_data.dropna(subset=['memory_used_mb', 'memory_size_mb']).copy()
    
    if memory_data.empty:
        st.info("No memory usage data available.")
        return
    
    # Ensure datetime column is timezone-naive
    memory_data = ensure_timezone_naive(memory_data)
    
    # Get memory metrics early so they're available in all code paths
    avg_memory = memory_analysis.get('avg_memory_used_mb', 0)
    max_memory = memory_analysis.get('max_memory_used_mb', 0)
    memory_size = memory_data['memory_size_mb'].iloc[0] if not memory_data.empty else 128
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Create memory usage histogram
        if len(memory_data['memory_used_mb'].unique()) > 1:
            fig = px.histogram(
                memory_data,
                x='memory_used_mb',
                nbins=30,
                title='Memory Usage Distribution',
                labels={'memory_used_mb': 'Memory Used (MB)', 'count': 'Frequency'},
                color_discrete_sequence=['#007bff']
            )
            
            # Add a vertical line for the average memory used
            avg_memory = memory_analysis.get('avg_memory_used_mb', 0)
            fig.add_vline(
                x=avg_memory,
                line_dash="dash",
                line_color="#fd7e14",
                annotation_text=f"Avg: {avg_memory:.1f} MB",
                annotation_position="top right"
            )
        else:
            # If all memory values are the same, create a simple bar chart instead
            single_value = memory_data['memory_used_mb'].iloc[0]
            count = len(memory_data)
            fig = px.bar(
                x=['Memory Used'],
                y=[count],
                title='Memory Usage Distribution',
                labels={'x': 'Memory Used (MB)', 'y': 'Count'},
                color_discrete_sequence=['#007bff']
            )
            fig.update_layout(
                annotations=[
                    dict(
                        x='Memory Used',
                        y=count,
                        text=f"{single_value:.1f} MB",
                        showarrow=False,
                        yshift=10
                    )
                ]
            )
        
        # Add a vertical line for the p95 memory used
        p95_memory = memory_analysis.get('p95_memory_used_mb', 0)
        fig.add_vline(
            x=p95_memory,
            line_dash="dash",
            line_color="#28a745",
            annotation_text=f"P95: {p95_memory:.1f} MB",
            annotation_position="top right"
        )
        
        # Add a vertical line for the configured memory size
        fig.add_vline(
            x=memory_size,
            line_dash="solid",
            line_color="#dc3545",
            annotation_text=f"Configured: {memory_size:.0f} MB",
            annotation_position="top left"
        )
        
        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis_title="Memory Used (MB)",
            yaxis_title="Number of Invocations"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Display memory metrics
        st.markdown("### Memory Metrics")
        
        # Memory size
        st.metric(
            "Configured Memory",
            f"{memory_size:.0f} MB"
        )
        
        # Average memory used
        st.metric(
            "Average Memory Used",
            f"{avg_memory:.1f} MB",
            f"{avg_memory / memory_size * 100:.1f}% of configured"
        )
        
        # Max memory used
        st.metric(
            "Max Memory Used",
            f"{max_memory:.1f} MB",
            f"{max_memory / memory_size * 100:.1f}% of configured"
        )
        
        # P95 memory used
        st.metric(
            "P95 Memory Used",
            f"{p95_memory:.1f} MB",
            f"{p95_memory / memory_size * 100:.1f}% of configured"
        )
    
    # Memory optimization recommendation
    recommendation = memory_analysis.get('recommendation', {})
    if recommendation:
        action = recommendation.get('action')
        current_size = recommendation.get('current_size')
        recommended_size = recommendation.get('recommended_size', current_size)
        
        if action == 'decrease':
            savings = recommendation.get('savings_percentage', 0) * 100
            st.success(
                f"**Memory Optimization Recommendation:** Decrease memory from {current_size} MB to "
                f"{recommended_size} MB to save approximately {savings:.1f}% in costs."
            )
        elif action == 'increase':
            st.warning(
                f"**Memory Optimization Recommendation:** Increase memory from {current_size} MB to "
                f"{recommended_size} MB to potentially improve performance."
            )
        else:
            st.info(
                "**Memory Optimization Recommendation:** Current memory configuration appears optimal."
            )
    
    # Memory usage over time
    if 'datetime' in memory_data.columns:
        st.subheader("Memory Usage Over Time")
        
        # Create a time-series chart of memory usage
        fig = px.scatter(
            memory_data,
            x='datetime',
            y='memory_used_mb',
            color='cold_start' if 'cold_start' in memory_data.columns else None,
            title='Memory Usage Over Time',
            labels={
                'datetime': 'Time',
                'memory_used_mb': 'Memory Used (MB)',
                'cold_start': 'Cold Start'
            },
            color_discrete_map={True: '#fd7e14', False: '#007bff'}
        )
        
        # Add a horizontal line for the configured memory size
        fig.add_hline(
            y=memory_size,
            line_dash="dash",
            line_color="#dc3545",
            annotation_text=f"Configured: {memory_size:.0f} MB",
            annotation_position="top right"
        )
        
        fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis_title="Time",
            yaxis_title="Memory Used (MB)"
        )
        
        st.plotly_chart(fig, use_container_width=True)

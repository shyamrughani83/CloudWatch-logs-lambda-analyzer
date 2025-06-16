"""
Metrics Dashboard component for CloudWatch Logs Analyzer.
Displays performance metrics and key indicators.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Any


def render_metrics_dashboard(metrics: Dict[str, Any]) -> None:
    """
    Render the metrics dashboard with key performance indicators.
    
    Args:
        metrics: Dictionary with calculated metrics
    """
    if not metrics:
        st.info("No metrics available. Please fetch log data first.")
        return
    
    st.subheader("Performance Overview")
    
    # Create metrics cards in a grid
    col1, col2, col3, col4 = st.columns(4)
    
    # Invocations
    with col1:
        render_metric_card(
            "Total Invocations",
            metrics.get('total_invocations', 0),
            "",
            "blue"
        )
    
    # Success Rate
    with col2:
        success_rate = metrics.get('success_rate', 0) * 100
        color = "green" if success_rate >= 99 else "orange" if success_rate >= 95 else "red"
        render_metric_card(
            "Success Rate",
            f"{success_rate:.2f}%",
            f"{metrics.get('error_rate', 0) * 100:.2f}% errors",
            color
        )
    
    # Avg Duration
    with col3:
        avg_duration = metrics.get('avg_duration_ms', 0)
        color = "green" if avg_duration < 100 else "orange" if avg_duration < 500 else "red"
        render_metric_card(
            "Avg Duration",
            f"{avg_duration:.2f} ms",
            f"P95: {metrics.get('p95_duration_ms', 0):.2f} ms",
            color
        )
    
    # Memory Utilization
    with col4:
        memory_util = metrics.get('memory_utilization', 0) * 100
        color = "orange" if memory_util < 40 else "green" if memory_util < 80 else "red"
        render_metric_card(
            "Memory Utilization",
            f"{memory_util:.2f}%",
            f"Max: {metrics.get('max_memory_used_mb', 0):.0f} MB",
            color
        )
    
    # Second row of metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Cold Starts
    with col1:
        cold_start_rate = metrics.get('cold_start_rate', 0) * 100
        color = "green" if cold_start_rate < 5 else "orange" if cold_start_rate < 15 else "red"
        render_metric_card(
            "Cold Start Rate",
            f"{cold_start_rate:.2f}%",
            f"{metrics.get('cold_start_count', 0)} cold starts",
            color
        )
    
    # Max Duration
    with col2:
        max_duration = metrics.get('max_duration_ms', 0)
        color = "green" if max_duration < 1000 else "orange" if max_duration < 5000 else "red"
        render_metric_card(
            "Max Duration",
            f"{max_duration:.2f} ms",
            "",
            color
        )
    
    # Error Count
    with col3:
        error_count = int(metrics.get('total_invocations', 0) * metrics.get('error_rate', 0))
        color = "green" if error_count == 0 else "orange" if error_count < 5 else "red"
        render_metric_card(
            "Error Count",
            f"{error_count}",
            "",
            color
        )
    
    # Billed Duration
    with col4:
        if 'avg_billed_duration_ms' in metrics:
            billed_duration = metrics.get('avg_billed_duration_ms', 0)
            render_metric_card(
                "Avg Billed Duration",
                f"{billed_duration:.2f} ms",
                "",
                "blue"
            )
        else:
            render_metric_card(
                "Billed Duration",
                "N/A",
                "",
                "gray"
            )


def render_metric_card(title: str, value: Any, subtitle: str = "", color: str = "blue") -> None:
    """
    Render a metric card with title, value, and optional subtitle.
    
    Args:
        title: Title of the metric
        value: Value to display
        subtitle: Optional subtitle or additional context
        color: Color for the value (green, orange, red, blue, gray)
    """
    # Define colors
    colors = {
        "green": "#28a745",
        "orange": "#fd7e14",
        "red": "#dc3545",
        "blue": "#007bff",
        "gray": "#6c757d"
    }
    
    # Create card with custom HTML/CSS
    st.markdown(
        f"""
        <div style="
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            padding: 1rem;
            margin-bottom: 1rem;
            background-color: white;
            height: 100%;
        ">
            <h4 style="
                margin-top: 0;
                margin-bottom: 0.5rem;
                font-size: 0.9rem;
                color: #6c757d;
            ">{title}</h4>
            <p style="
                font-size: 1.5rem;
                font-weight: 500;
                margin-bottom: 0.25rem;
                color: {colors.get(color, colors['blue'])};
            ">{value}</p>
            <p style="
                font-size: 0.8rem;
                color: #6c757d;
                margin-bottom: 0;
            ">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_performance_recommendations(metrics: Dict[str, Any]) -> None:
    """
    Render performance recommendations based on metrics.
    
    Args:
        metrics: Dictionary with calculated metrics
    """
    if not metrics:
        return
    
    st.subheader("Performance Recommendations")
    
    recommendations = []
    
    # Memory recommendations
    memory_analysis = metrics.get('memory_analysis', {})
    if memory_analysis:
        memory_rec = memory_analysis.get('recommendation', {})
        if memory_rec:
            action = memory_rec.get('action')
            if action == 'decrease':
                recommendations.append({
                    'title': 'Memory Optimization',
                    'description': f"Consider decreasing memory from {memory_rec.get('current_size')} MB to {memory_rec.get('recommended_size')} MB to save costs.",
                    'impact': f"Potential savings: {memory_rec.get('savings_percentage', 0) * 100:.1f}%",
                    'priority': 'high'
                })
            elif action == 'increase':
                recommendations.append({
                    'title': 'Memory Optimization',
                    'description': f"Consider increasing memory from {memory_rec.get('current_size')} MB to {memory_rec.get('recommended_size')} MB to improve performance.",
                    'impact': "May reduce duration and improve overall performance",
                    'priority': 'medium'
                })
    
    # Cold start recommendations
    cold_start_analysis = metrics.get('cold_start_analysis', {})
    if cold_start_analysis:
        cold_start_rate = cold_start_analysis.get('cold_start_rate', 0)
        cold_start_impact = cold_start_analysis.get('cold_start_impact', 0)
        
        if cold_start_rate > 0.1 and cold_start_impact > 1.0:
            recommendations.append({
                'title': 'Cold Start Optimization',
                'description': "Consider using Provisioned Concurrency to reduce cold starts.",
                'impact': f"Cold starts are {cold_start_impact:.1f}x slower than warm starts",
                'priority': 'high' if cold_start_rate > 0.2 else 'medium'
            })
    
    # Duration recommendations
    p95_duration = metrics.get('p95_duration_ms', 0)
    if p95_duration > 1000:
        recommendations.append({
            'title': 'Duration Optimization',
            'description': "Function duration is high. Consider optimizing code or increasing memory.",
            'impact': f"P95 duration: {p95_duration:.2f} ms",
            'priority': 'medium' if p95_duration < 3000 else 'high'
        })
    
    # Error recommendations
    error_rate = metrics.get('error_rate', 0)
    if error_rate > 0.01:
        recommendations.append({
            'title': 'Error Handling',
            'description': "Function has a high error rate. Review error patterns and implement better error handling.",
            'impact': f"Error rate: {error_rate * 100:.2f}%",
            'priority': 'high' if error_rate > 0.05 else 'medium'
        })
    
    # Display recommendations
    if recommendations:
        for i, rec in enumerate(recommendations):
            priority_color = {
                'high': '#dc3545',
                'medium': '#fd7e14',
                'low': '#28a745'
            }.get(rec['priority'], '#6c757d')
            
            st.markdown(
                f"""
                <div style="
                    border-left: 4px solid {priority_color};
                    padding: 0.5rem 1rem;
                    margin-bottom: 1rem;
                    background-color: #f8f9fa;
                ">
                    <h5 style="margin-top: 0;">{rec['title']}</h5>
                    <p style="margin-bottom: 0.5rem;">{rec['description']}</p>
                    <p style="
                        font-size: 0.8rem;
                        color: #6c757d;
                        margin-bottom: 0;
                    "><strong>Impact:</strong> {rec['impact']}</p>
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.info("No performance recommendations at this time.")

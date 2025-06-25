"""
Helper functions for CloudWatch Logs Analyzer
"""

import pandas as pd
import numpy as np
import datetime
import streamlit as st
from typing import Any, Dict, List, Optional, Union

def ensure_timezone_naive(dt: Any) -> Any:
    """
    Ensure datetime is timezone naive for compatibility.
    
    Args:
        dt (Any): Datetime object or any other object
        
    Returns:
        Any: Timezone naive datetime or original object
    """
    if isinstance(dt, datetime.datetime) and hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt

def convert_for_streamlit_display(value: Any) -> Any:
    """
    Convert values to formats compatible with Streamlit display.
    
    Args:
        value (Any): Value to convert
        
    Returns:
        Any: Converted value
    """
    if isinstance(value, (np.int64, np.int32)):
        return int(value)
    elif isinstance(value, (np.float64, np.float32)):
        return float(value)
    elif isinstance(value, datetime.datetime):
        return ensure_timezone_naive(value)
    elif isinstance(value, (list, tuple)) and value and isinstance(value[0], dict):
        return [convert_for_streamlit_display(item) for item in value]
    elif isinstance(value, dict):
        return {k: convert_for_streamlit_display(v) for k, v in value.items()}
    return value

def ensure_arrow_compatible(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure DataFrame is compatible with Arrow (used by Streamlit).
    
    Args:
        df (pd.DataFrame): DataFrame to convert
        
    Returns:
        pd.DataFrame: Arrow-compatible DataFrame
    """
    if df.empty:
        return df
        
    # Create a copy to avoid modifying the original
    result = df.copy()
    
    # Convert numpy int/float types to Python native types
    for col in result.select_dtypes(include=['int']).columns:
        result[col] = result[col].astype('int64')
        
    for col in result.select_dtypes(include=['float']).columns:
        result[col] = result[col].astype('float64')
    
    # Handle datetime columns
    for col in result.select_dtypes(include=['datetime']).columns:
        result[col] = result[col].apply(ensure_timezone_naive)
    
    return result

def safe_display(df: pd.DataFrame) -> pd.DataFrame:
    """
    Safely display a DataFrame in Streamlit by ensuring compatibility.
    
    Args:
        df (pd.DataFrame): DataFrame to display
        
    Returns:
        pd.DataFrame: Safe-to-display DataFrame
    """
    if df.empty:
        return df
        
    # First ensure Arrow compatibility
    df = ensure_arrow_compatible(df)
    
    # Then convert any remaining problematic values
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(convert_for_streamlit_display)
    
    return df

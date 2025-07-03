from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import json
import traceback
from app.utils.aws_helper import test_aws_connection, get_boto3_session, get_log_groups, get_lambda_functions, invoke_lambda_function, get_log_events
from app.utils.log_helper import get_log_streams
from app.forms import AWSConnectionForm

main_bp = Blueprint('main', __name__)

@main_bp.route('/', methods=['GET', 'POST'])
def index():
    form = AWSConnectionForm()
    
    if form.validate_on_submit():
        region = form.region.data
        profile = form.profile.data if form.profile.data else None
        
        # Test AWS connection
        connection_result = test_aws_connection(region, profile)
        
        if connection_result['success']:
            # Store AWS connection info in session
            session['aws_region'] = region
            session['aws_profile'] = profile
            flash('Successfully connected to AWS!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash(f'Failed to connect to AWS: {connection_result["error"]}', 'danger')
    
    return render_template('index.html', form=form)

@main_bp.route('/dashboard')
def dashboard():
    # Check if AWS connection is established
    if 'aws_region' not in session:
        flash('Please connect to AWS first', 'warning')
        return redirect(url_for('main.index'))
    
    region = session.get('aws_region')
    profile = session.get('aws_profile')
    
    try:
        # Get log groups directly
        session_obj = get_boto3_session(region, profile)
        logs_client = session_obj.client('logs')
        lambda_client = session_obj.client('lambda')
        
        # Get log groups - using limit=50 as per AWS constraints
        log_groups = []
        log_response = logs_client.describe_log_groups(limit=50)
        for log_group in log_response.get('logGroups', []):
            log_groups.append({
                'name': log_group.get('logGroupName', 'Unknown'),
                'arn': log_group.get('arn', ''),
                'storedBytes': log_group.get('storedBytes', 0),
                'creationTime': log_group.get('creationTime', 0) / 1000
            })
        
        # Get Lambda functions - using MaxItems=50 for consistency
        lambda_functions = []
        lambda_response = lambda_client.list_functions(MaxItems=50)
        for function in lambda_response.get('Functions', []):
            lambda_functions.append({
                'name': function.get('FunctionName', 'Unknown'),
                'runtime': function.get('Runtime', 'N/A'),
                'memory': function.get('MemorySize', 0),
                'timeout': function.get('Timeout', 0),
                'lastModified': function.get('LastModified', 'N/A')
            })
        
        print(f"Found {len(log_groups)} log groups and {len(lambda_functions)} Lambda functions")
        
        # Use the simplified dashboard template
        return render_template('dashboard_simple.html', 
                              log_groups=log_groups,
                              lambda_functions=lambda_functions,
                              region=region)
    except Exception as e:
        import traceback
        print(f"Dashboard error: {str(e)}")
        print(traceback.format_exc())
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@main_bp.route('/logs')
def logs():
    # Redirect to dashboard with logs section
    flash('Logs section is now integrated into the Dashboard', 'info')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/lambda')
def lambda_functions():
    # Redirect to dashboard with lambda section
    flash('Lambda functions section is now integrated into the Dashboard', 'info')
    return redirect(url_for('main.dashboard'))

@main_bp.route('/api/log-groups')
def api_log_groups():
    if 'aws_region' not in session:
        return jsonify({'success': False, 'error': 'No AWS connection'}), 401
    
    region = session.get('aws_region')
    profile = session.get('aws_profile')
    
    try:
        log_groups = get_log_groups(region, profile)
        return jsonify({'success': True, 'data': log_groups})
    except Exception as e:
        print(f"Error fetching log groups: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/lambda-functions')
def api_lambda_functions():
    """Get all Lambda functions in the current region"""
    if 'aws_region' not in session:
        return jsonify({'success': False, 'error': 'No AWS connection'}), 401
    
    region = session.get('aws_region')
    profile = session.get('aws_profile')
    
    try:
        # Direct approach with minimal processing for reliability
        session_obj = get_boto3_session(region, profile)
        lambda_client = session_obj.client('lambda')
        
        # Get functions with correct pagination limit
        functions = []
        response = lambda_client.list_functions(MaxItems=50)
        
        for function in response.get('Functions', []):
            functions.append({
                'name': function.get('FunctionName', 'Unknown'),
                'arn': function.get('FunctionArn', ''),
                'runtime': function.get('Runtime', 'N/A'),
                'memory': function.get('MemorySize', 0),
                'timeout': function.get('Timeout', 0),
                'lastModified': function.get('LastModified', 'N/A'),
                'handler': function.get('Handler', 'N/A'),
                'description': function.get('Description', ''),
                'role': function.get('Role', 'N/A')
            })
        
        print(f"Successfully fetched {len(functions)} Lambda functions")
        return jsonify({'success': True, 'data': functions})
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error fetching lambda functions: {str(e)}")
        print(error_trace)
        return jsonify({
            'success': False, 
            'error': str(e),
            'traceback': error_trace
        }), 500
        
@main_bp.route('/api/log-streams')
def api_log_streams():
    if 'aws_region' not in session:
        return jsonify({'success': False, 'error': 'No AWS connection'}), 401
    
    region = session.get('aws_region')
    profile = session.get('aws_profile')
    log_group_name = request.args.get('log_group_name')
    
    if not log_group_name:
        return jsonify({'success': False, 'error': 'Log group name is required'}), 400
    
    try:
        log_streams = get_log_streams(region, log_group_name, profile)
        return jsonify({'success': True, 'data': log_streams})
    except Exception as e:
        print(f"Error fetching log streams: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500
        
@main_bp.route('/api/invoke-lambda', methods=['POST'])
def api_invoke_lambda():
    if 'aws_region' not in session:
        return jsonify({'success': False, 'error': 'No AWS connection'}), 401
    
    region = session.get('aws_region')
    profile = session.get('aws_profile')
    
    data = request.json
    function_name = data.get('function_name')
    payload = data.get('payload', '{}')
    
    if not function_name:
        return jsonify({'success': False, 'error': 'Function name is required'}), 400
    
    try:
        result = invoke_lambda_function(region, function_name, payload, profile)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/log-events')
def api_log_events():
    if 'aws_region' not in session:
        return jsonify({'success': False, 'error': 'No AWS connection'}), 401
    
    region = session.get('aws_region')
    profile = session.get('aws_profile')
    log_group_name = request.args.get('log_group_name')
    log_stream_name = request.args.get('log_stream_name')
    
    if not log_group_name or not log_stream_name:
        return jsonify({'success': False, 'error': 'Log group name and log stream name are required'}), 400
    
    try:
        log_events = get_log_events(region, log_group_name, log_stream_name, profile)
        return jsonify({'success': True, 'data': log_events})
    except Exception as e:
        print(f"Error fetching log events: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/debug-lambda')
def api_debug_lambda():
    """Debug endpoint to help diagnose Lambda loading issues"""
    if 'aws_region' not in session:
        return jsonify({'success': False, 'error': 'No AWS connection'}), 401
    
    region = session.get('aws_region')
    profile = session.get('aws_profile')
    
    try:
        # Get raw Lambda functions data with minimal processing
        session_obj = get_boto3_session(region, profile)
        lambda_client = session_obj.client('lambda')
        
        # Direct API call with correct pagination limit
        response = lambda_client.list_functions(MaxItems=20)
        
        # Return raw response for debugging
        return jsonify({
            'success': True, 
            'raw_response': str(response),
            'functions_count': len(response.get('Functions', [])),
            'region': region,
            'profile': profile
        })
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Debug Lambda error: {str(e)}")
        print(error_trace)
        return jsonify({
            'success': False, 
            'error': str(e),
            'traceback': error_trace,
            'region': region,
            'profile': profile
        }), 500

from flask import Flask
from flask_bootstrap import Bootstrap
import os
import logging
import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    app = Flask(__name__)
    
    # Get configuration from environment variables or use defaults
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'cloudwatch-logs-lambda-analyzer-secret-key')
    app.config['AWS_REGION'] = os.environ.get('AWS_REGION', 'us-east-1')
    
    logger.info(f"Initializing app with AWS region: {app.config['AWS_REGION']}")
    
    # Initialize Flask extensions
    Bootstrap(app)
    
    # Register custom filters
    @app.template_filter('strftime')
    def _jinja2_filter_datetime(timestamp, fmt=None):
        if timestamp is None:
            return ''
        if fmt is None:
            fmt = '%Y-%m-%d %H:%M:%S'
        return datetime.datetime.fromtimestamp(timestamp).strftime(fmt)
    
    # Register blueprints
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app

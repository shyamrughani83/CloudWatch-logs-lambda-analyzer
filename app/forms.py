from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional

class AWSConnectionForm(FlaskForm):
    region = SelectField('AWS Region', validators=[DataRequired()], 
                        choices=[
                            ('us-east-1', 'US East (N. Virginia)'),
                            ('us-east-2', 'US East (Ohio)'),
                            ('us-west-1', 'US West (N. California)'),
                            ('us-west-2', 'US West (Oregon)'),
                            ('af-south-1', 'Africa (Cape Town)'),
                            ('ap-east-1', 'Asia Pacific (Hong Kong)'),
                            ('ap-south-1', 'Asia Pacific (Mumbai)'),
                            ('ap-northeast-3', 'Asia Pacific (Osaka)'),
                            ('ap-northeast-2', 'Asia Pacific (Seoul)'),
                            ('ap-southeast-1', 'Asia Pacific (Singapore)'),
                            ('ap-southeast-2', 'Asia Pacific (Sydney)'),
                            ('ap-northeast-1', 'Asia Pacific (Tokyo)'),
                            ('ca-central-1', 'Canada (Central)'),
                            ('eu-central-1', 'Europe (Frankfurt)'),
                            ('eu-west-1', 'Europe (Ireland)'),
                            ('eu-west-2', 'Europe (London)'),
                            ('eu-south-1', 'Europe (Milan)'),
                            ('eu-west-3', 'Europe (Paris)'),
                            ('eu-north-1', 'Europe (Stockholm)'),
                            ('me-south-1', 'Middle East (Bahrain)'),
                            ('sa-east-1', 'South America (São Paulo)')
                        ])
    profile = StringField('AWS Profile (optional)', validators=[Optional()])
    submit = SubmitField('Connect')

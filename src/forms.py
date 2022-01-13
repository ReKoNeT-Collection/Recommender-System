from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, RadioField
from wtforms.validators import DataRequired

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class RecommendSimilarMM(FlaskForm):
    material_id = StringField('Material Number', validators=[DataRequired()])
    tech = RadioField('Technologie:', choices=[('0','Any'),('1','Milling'),('2','Turning')], default='0')
    submit = SubmitField('Search')

class SearchByMachine(FlaskForm):
    machine_id = StringField('Maschinenbezeichnung', validators=[DataRequired()])
    submit = SubmitField('Suchen')

class EvaluationForm(FlaskForm):
    btn_yes = SubmitField('Yes')
    btn_no = SubmitField('No')

class OurForm(FlaskForm):
    material = StringField('foo')
    machine = StringField('bar')
    feedback = StringField('feedback')
    btn_yes = SubmitField('Yes')
    btn_no = SubmitField('No')

class Feedback(FlaskForm):
    material = StringField('material')
    machine = StringField('machine')
    feedback = BooleanField('feedback')
    btn_yes = SubmitField('Yes')
    btn_no = SubmitField('No')


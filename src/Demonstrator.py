from pathlib import Path
from datetime import datetime
import PrepareData as prepD
import numpy as np
import pandas as pd
import pickle
import scipy.sparse as sparse
import implicit
import Recommender as rs
from pathlib import Path
import random as rd
import matplotlib.pyplot as plt
from flask import Flask, request, Response, render_template, session, flash, abort
import os
import json
import re
from flask_sqlalchemy import SQLAlchemy
from forms import RegistrationForm, RecommendSimilarMM, EvaluationForm, OurForm, SearchByMachine


app = Flask(__name__)

app.config['SECRET_KEY'] = '962fe5aa39bb52af0f2872ab58bc0580'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)


class MatchFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material  = db.Column(db.Integer, nullable=False)
    machine = db.Column(db.String(120), nullable=False)
    feedback = db.Column(db.Boolean, nullable=False)
    date_of_feedback = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"ID:'{self.id}', Material:'{self.material}', Machine: '{self.machine}', Feedback:'{self.feedback}', Datum:'{self.date_of_feedback}')"

class SimMaterialFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_material  = db.Column(db.Integer, nullable=False)
    second_material = db.Column(db.Integer, nullable=False)
    feedback = db.Column(db.Boolean, nullable=False)
    date_of_feedback = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"ID:'{self.id}', Material 1:'{self.first_material}', Material 2: '{self.second_material}', Feedback:'{self.feedback}', Datum:'{self.date_of_feedback}')"

class SimMachineFeedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_machine  = db.Column(db.String(120), nullable=False)
    second_machine = db.Column(db.String(120), nullable=False)
    feedback = db.Column(db.Boolean, nullable=False)
    date_of_feedback = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"ID:'{self.id}', Maschine 1:'{self.first_machine}', Maschine 2: '{self.second_machine}', Feedback:'{self.feedback}', Datum:'{self.date_of_feedback}')"

recmodel = None

#########################################################################
#REST Implementierung

@app.before_request
def session_handling():
    if request.form and ('submit' in request.form) and request.form['submit'] == 'logout':
        session['logged_in'] = False
        return render_template('login.html')     

    elif not session.get('logged_in'):
        if request.form and ('password' in request.form) and request.form['password'] == 'password' and request.form['username'] == 'user':
            session['logged_in'] = True
        elif request.endpoint != 'static':
            return render_template('login.html')    


@app.route('/train', methods=['POST'])
def rest_trainnewmodel2():
    #Lese CSV ein
    if 'mycsv' not in request.files:
        return json.dumps("Error 534: No File uploaded")
            
    file = request.files['mycsv']
    if file.filename == '':
        return json.dumps("Error 534: CSV Parameter existent but could not be loaded")
    if file:
        try:       
            global recmodel 

            pr = prepD.PrepareData()            
            pr.preapreFromFile(file)
            recmodel = rs.RecommenderByTech()
            recmodel.train(pr.getInteractionTable())

            flash(f'Model trained!', 'success')
            answer = json.dumps("Done")
        except Exception as err:
            answer = json.dumps("Error 534: " + str(err))
            flash(f'Fehler 534, Modell was not trained!', 'danger')
        return answer

    flash(f'Fehler 534, Modell was not trained!', 'danger')
    return json.dumps("Error 534")

#HTML-Frontpage
@app.route('/', methods = ['GET','POST'])
def search_machines():
    form = RecommendSimilarMM()
    form_ev = EvaluationForm()
    rec_av = False

    material_id = form.material_id.data
    technologie = form.tech.data
    tech = 0

    try:
        tech = int(technologie)    
    except:
        None

    if material_id is not None:
        try:
            material_id = int(material_id)
            result = recmodel.recommend(material_id, techProvided=tech)
            recommendation = list([rec[0] for rec in result[0]])
            rec_av = True
        except Exception as err:
            rec_av = False
            print("Recommendation failed")

        if rec_av == True:
            response = pd.DataFrame()
            response['Maschine'] = recommendation
            response['Plausibel'] = np.nan
            df = response
            response2 = pd.DataFrame()
            response2['Maschine'] = recmodel.interactions.loc[recmodel.interactions.PartID == material_id].WorkcenterType
            df2 = response2

            ### Material
            itersimmaterial = iter(result[1])
            simmaterial = list([str(rec[0]) for rec in itersimmaterial])

            try:
                simmaterial.remove(str(material_id))
            except:
                del simmaterial[-1]

            df3 = pd.DataFrame()
            df3['Material'] = simmaterial
            df3['Plausibel'] = np.nan

            flash(f'Search for material {form.material_id.data} successfull', 'success')

    if rec_av == False:
        df = pd.DataFrame()
        df2 = pd.DataFrame()
        df3 = pd.DataFrame()
        if recmodel == None:
            flash(f'Modell not trained!', 'danger')
        else:
            flash(f'Modell trained!', 'success')
            if rec_av == False and material_id is not None:
                flash(f'Search for material {form.material_id.data} nit successfull', 'danger')

    # link_column is the column that I want to add a button to
    return render_template("search_machines.html",
                        column_names=df.columns.values, row_data=list(df.values.tolist()),
                        column_names2=df2.columns.values, row_data2=list(df2.values.tolist()),
                        column_names3=df3.columns.values, row_data3=list(df3.values.tolist()),
                        form=form, form_ev=form_ev, zip =zip,
                        link_column="Plausibel")#, zip=zip)

### HTML für suche ähnlicher Materialien auf Basis der Maschinenbezeichnung
@app.route('/search_materials', methods = ['GET','POST'])
def search_materials():
    form = SearchByMachine()
    form_ev = EvaluationForm()

    if form.validate_on_submit():
        flash(f'Search for machine {form.machine_id.data} successfull', 'success')

    machine_id = form.machine_id.data
    if machine_id is not None:
        try:
            recommendation = list([rec[0] for rec in recmodel_reversed.recommend(machine_id)])
        except:
            recommendation = list()

        df = pd.DataFrame()
        df['Material'] = recommendation
        df['Fertigungsdauer'] = np.nan
        df['Plausibel'] = np.nan

        try:
            materialliste = prepD.PrepareData.get_usedMaterialien(trainset_big, machine_id)
            #Auswahl von maximal 400 zufälligen Material-IDs aus materialliste aus Performancegründen
            if len(materialliste) > 400:
                sampling = rd.choices(materialliste, k = 400)
                materialliste = sorted(sampling)
            df2 = pd.DataFrame()
            df2['Material'] = materialliste
        except:
            df2 = pd.DataFrame()

        itersimmachine = iter(recmodel.similar_items(machine_id))
        simmachine = list([str(rec[0]) for rec in itersimmachine])

        try:
            simmachine.remove(str(machine_id))
        except:
            del simmachine[-1]

        df3 = pd.DataFrame()
        df3['Maschine'] = simmachine
        df3['Plausibel'] = np.nan
    else:
        df = pd.DataFrame()
        df2 = pd.DataFrame()
        df3 = pd.DataFrame()

    # link_column is the column that I want to add a button to
    return render_template("search_materials.html",
                           column_names=df.columns.values, row_data=list(df.values.tolist()),
                           column_names2=df2.columns.values, row_data2=list(df2.values.tolist()),
                           column_names3=df3.columns.values, row_data3=list(df3.values.tolist()),
                           form=form, form_ev=form_ev, zip =zip,
                           link_column="Plausibel")#, zip=zip)

@app.route('/sim_machines', methods = ['GET','POST'])
def sim_machine():
    form = SearchByMachine()
    form_ev = EvaluationForm()
    df = pd.DataFrame()

    if form.validate_on_submit():
        flash(f'Suche nach ├ñhnlichen Maschinen f├╝r {form.machine_id.data} erfolgreich', 'success')

    machine_id = form.machine_id.data
    if not machine_id == None:
        if not session.get('logged_in'):
            return abort(403)
        elif recmodel == None:
            return "Recommender not trained",404
        else:
            itersimmachine = iter(recmodel.similar_items(machine_id))

            simmachine = list([str(rec[0]) for rec in itersimmachine])

            try:
                simmachine.remove(str(machine_id))
            except:
                del simmachine[-1]

            df['Maschine'] = simmachine
            df['Plausibel'] = np.nan

    return render_template("sim_machines.html", column_names=df.columns.values, row_data=list(df.values.tolist()),
                           zip=zip, form=form, form_ev=form_ev, link_column="Plausibel")

@app.route('/mftodb/', methods=['POST'])
def match_feedback_to_db():
#    machine = request.form['machine']
    if request.method == "POST":
        if request.form['feedback'] == 'true':
            rec_feedback = True
        elif request.form['feedback'] == 'false':
            rec_feedback = False
        else:
            rec_feedback = None
        ret = MatchFeedback(material=request.form['material'], machine=request.form['machine'], feedback=rec_feedback)
        db.session.add(ret)
        db.session.commit()
        return 'success'

@app.route('/mmttodb/', methods=['POST'])
def sim_mat_feedback_to_db():
    if request.method == "POST":
        if request.form['feedback'] == 'true':
            rec_feedback = True
        elif request.form['feedback'] == 'false':
            rec_feedback = False
        else:
            rec_feedback = None
        ret = SimMaterialFeedback(first_material=request.form['first_material'], second_material=request.form['second_material'], feedback=rec_feedback)
        db.session.add(ret)
        db.session.commit()
        return 'success'

@app.route('/mmctodb/', methods=['POST'])
def sim_mac_feedback_to_db():
    if request.method == "POST":
        if request.form['feedback'] == 'true':
            rec_feedback = True
        elif request.form['feedback'] == 'false':
            rec_feedback = False
        else:
            rec_feedback = None
        ret = SimMachineFeedback(first_machine=request.form['first_machine'], second_machine=request.form['second_machine'], feedback=rec_feedback)
        db.session.add(ret)
        db.session.commit()
        return 'success'

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')


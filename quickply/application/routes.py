from application import app
from flask import render_template,request,json,Response
from werkzeug.utils import secure_filename
from application import db
from application import controller as gp
from google.oauth2.credentials import Credentials
import google.oauth2.credentials
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import flask
import os.path
import subprocess
import pandas as pd
from datetime import date
from flask import flash
import time
from multiprocessing import Pool
from multiprocessing import cpu_count

app.config['SECRET_KEY']="secret_key"

@app.route("/")
@app.route("/index")
@app.route("/home")
def index():
    return render_template("index.html",index=True)

@app.route("/login", methods=['GET','POST'])
def login():  
    print("Login")
    return render_template("login.html",login=True)

@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    username = request.form.get('username')
    password = request.form.get('password')
    print("Username is %s"% username)
    print("Password is %s"% password)
    response=db.checkUser(username)
    print("response in routes is" + str(response))
    if response['status'] == 'fail':
        flash("No user exists! Please register", "warning")
        return render_template("register.html")
    elif password!=response['data']['password']:
        flash("Wrong password! Re-enter", "danger")
        return render_template("login.html")
    else:
        flash("Successfully logged in! Here is your Dashboard", "success")
        return render_template("dashboard.html",dashboard=True)

@app.route('/gmail', methods=['GET','POST'])
def gmail():    
    return flask.redirect("/callauth")

@app.route('/callauth')
def callauth():
    creds = None
    if 'credentials' in flask.session:
        creds = google.oauth2.credentials.Credentials(
            **flask.session['credentials'])
    else:
        return flask.redirect('authorize')

    # Load the credentials from the session.

    service = build('gmail', 'v1', credentials=creds)
    messages = gp.filterEmails(service)
    print(messages)
    flash("Status of the jobs are updated successfully from email","success")
    return render_template("dashboard.html", dashboard=True)
    
@app.route('/authorize')
def authorize():
    # Create a flow instance to manage the OAuth 2.0 Authorization Grant Flow
    # steps.
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'application/static/credentials/credentials.json', scopes="https://www.googleapis.com/auth/gmail.readonly")

    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    authorization_url, state = flow.authorization_url(
        # This parameter enables offline access which gives your application
        # an access token and a refresh token for the user's credentials.
        access_type='offline',
        # This parameter enables incremental auth.
        include_granted_scopes='true')
    # Store the state in the session so that the callback can verify the
    # authorization server response.
    print("state is")
    print(state)
    flask.session['state'] = state
    return flask.redirect(authorization_url)


@app.route('/oauth2callback')
def oauth2callback():
    # Specify the state when creating the flow in the callback so that it can
    # verify the authorization server response.

    state = flask.session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'application/static/credentials/credentials.json',
        scopes='https://www.googleapis.com/auth/gmail.readonly',
        state=state)
    flow.redirect_uri = flask.url_for('oauth2callback', _external=True)

    # Use the authorization server's response to fetch the OAuth 2.0 tokens.
    authorization_response = flask.request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store the credentials in the session.
    credentials = flow.credentials

    flask.session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    return flask.redirect(flask.url_for('callauth'))

@app.route("/registersubmit", methods=["GET","POST"])
def registersubmit():
    email = request.form.get('email')
    response=db.checkUser(email)
    if response['status'] == 'success':
        flash('You are already registered, please login', 'warning')
        return render_template("login.html")
    else:
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        password = request.form.get('password')
        phonenumber = request.form.get('phonenumber')
        work = request.form.getlist('work')
        if work[0]=="Yes":
            work=1
        else:
            work=0
        sponsor = request.form.getlist('sponsor')
        if sponsor[0]=="Yes":
            sponsor=1
        else:
            sponsor=0
        file = request.form.get('file')
        print("fn is", firstname)
        print("ln is", lastname)
        print("email is", email)
        print("pass is", password)
        print("pn is", phonenumber)
        print("file is", file)
        resumeUrl="https://"+file
        lurl=request.form.get('linkedinurl')
        turl=request.form.get('twitterurl')
        gurl=request.form.get('githuburl')
        purl=request.form.get('portfoliourl')
        ourl=request.form.get('otherurl')
        age=request.form.getlist('age')
        if age:
            age_pass = age[0]
        else:
            age_pass = ""
        race=request.form.getlist('race')
        if race:
            race_pass = race[0]
        else:
            race_pass = ""
        gender=request.form.getlist('gender')
        if gender:
            gender_pass = race[0]
        else:
            gender_pass = ""
        vstatus=request.form.getlist('veteran')
        v_status=""
        if vstatus:
            if vstatus[0]=="Yes":
                v_status='1'
            elif vstatus[0]=="No":
                v_status='0'
            else:
                v_status='2'
        distatus=request.form.getlist('disability')
        dis_status=""
        if distatus:
            if distatus[0]=="Yes":
                dis_status='1'
            elif distatus[0]=="No":
                dis_status='0'
            else:
                dis_status='2'
        response= db.registerUser(firstname, lastname, phonenumber, email, password, work, sponsor, resumeUrl, lurl, turl, gurl, purl, ourl, age_pass, race_pass, gender_pass, v_status, dis_status)
        print("response is", str(response))
        print("db updated successfully")
        flash('You are now successfully registered! You can now login', 'success')
        return render_template("login.html",login=True)

@app.route("/register")
def register():
    return render_template("register.html",register=True)
	
@app.route("/fileupload", methods=['GET', 'POST'])
def fileupload():
    files = request.files['csvjobs']
    data = pd.read_csv(files)
    print("jobs data is", data)
    status="Applied"
    today = date.today()
    dateToInsert = today.strftime("%Y/%m/%d")
    for job in data.itertuples():
        email=job[1]
        companyName=job[2]
        jobTitle=job[3]
        jobId=job[4]
        db.jobApplied(email, companyName, jobTitle, status, dateToInsert, jobId)
    flash("Jobs are submitted", "success")
    return render_template("dashboard.html",dashboard=True)

@app.route("/displayjobs", methods=['GET', 'POST'])
def displayjobs():
    email=request.form.get('email_for_jobs')
    response=db.getAllJobsByEmail(email)
    return render_template("display.html",data=response['data'])

def f(x):
    while True:
        x*x

@app.route("/dummy", methods=['GET'])
def dummy():
    processes = cpu_count()
    print("utilizing %d cores\n".format(processes))
    pool = Pool(processes)
    pool.map(f, range(processes))
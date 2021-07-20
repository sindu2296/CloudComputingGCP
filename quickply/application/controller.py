import pickle
import os.path
import flask
from oauth2client.client import GoogleCredentials
from oauth2client.client import OAuth2WebServerFlow
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from email.mime.text import MIMEText
import google_auth_oauthlib.flow
import base64
from apiclient import errors
import pandas as pd
from application import db
import email
from bs4 import BeautifulSoup
from application import bert
import time

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
PREDICTIONS = ["Offered","In_Process","Reject"]

def ListMessagesMatchingQuery(service, user_id, query):
    txt =""
    try:
        response = service.users().messages().list(userId=user_id,
                q=query).execute()
        messages = []
        if 'messages' in response:
            messages = response.get('messages')

        for msg in messages : 
            msg = service.users().messages().get(userId=user_id, id=msg['id']).execute()
            payload = msg['payload']
            parts=payload["parts"]
            body=parts[0]["body"]
            data=body["data"]

            data = data.replace("-","+").replace("_","/")
            decoded_data = base64.b64decode(data)
            
            soup = BeautifulSoup(decoded_data,"lxml")
            pTags = soup.find_all("p")
            for ptag in pTags:
                txt=txt+" "+ptag.get_text()
            print(txt)
        return txt

    except errors.HttpError as error:
        print('An error occurred: %s' % error)

def filterEmails(service):
    messages =[]
    profile = service.users().getProfile(userId='me').execute()
    print(profile)
    jobs = db.getAllJobsByEmailAndStatusForGmail(profile['emailAddress'],"Applied")
    print(jobs[0].serialize())
    companyList = getCompanyNames(jobs,"Applied")

    for company in companyList:
        content = ListMessagesMatchingQuery(service,'me', query=company)
        messages.append(content)

    for job,message in zip(jobs,messages):
        time.sleep(3)
        predict=applyBert(message)
        updateJobs(job,PREDICTIONS[predict])
    return messages

def getCompanyNames(jobs,status):
    companies = []
    for job in jobs:
        companies.append(job.companyName)
    return companies

def updateJobs(job,status):
    job.status = status
    response=db.updateJobStatus(job)
    print("response: " +str(response))

def applyBert(message):
    return bert.predict_reject(message)

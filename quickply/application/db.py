from flask import Flask, jsonify, request, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
import sqlalchemy
from application import app
import json
import sys
import time

app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:quickply@/quickply?unix_socket=/cloudsql/modern-impulse-311322:us-central1:quickply"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app)


# User ORM for SQLAlchemy
class Profile(db.Model):
    firstName = db.Column(db.String, nullable=False)
    lastName = db.Column(db.String, nullable=False)
    phone = db.Column(db.String, nullable=False)
    emailId = db.Column(db.String, primary_key=True, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    linkedInUrl = db.Column(db.String, nullable=True)
    twitterUrl = db.Column(db.String, nullable=True)    
    githubUrl = db.Column(db.String, nullable=True)
    portfolioUrl = db.Column(db.String, nullable=True)
    otherUrl = db.Column(db.String, nullable=True)
    canLegallyWorkWithoutSponsorship = db.Column(db.Boolean, nullable=False)
    needSponsorshipInFuture = db.Column(db.Boolean, nullable=False)
    ageRange = db.Column(db.String, nullable=True)
    ethnicity = db.Column(db.String, nullable=True)
    gender = db.Column(db.String, nullable=True)
    veteranStatus = db.Column(db.String, nullable=True)
    disabilityStatus = db.Column(db.String, nullable=True)
    resumeUrl = db.Column(db.String, nullable=False)

    def serialize(self):
        return {"firstName": self.firstName,
        "lastName": self.lastName,
        "phone": self.phone,
        "emailId": self.emailId,
        "password":self.password, 
        "linkedInUrl": self.linkedInUrl, 
        "twitterUrl": self.twitterUrl,
        "githubUrl": self.githubUrl,
        "portfolioUrl": self.portfolioUrl,
        "otherUrl": self.otherUrl,
        "canLegallyWorkWithoutSponsorship": self.canLegallyWorkWithoutSponsorship,
        "needSponsorshipInFuture": self.needSponsorshipInFuture,"sourceFound": self.sourceFound,
        "ageRange": self.ageRange,
        "ethnicity": self.ethnicity,
        "gender": self.gender,
        "veteranStatus": self.veteranStatus,
        "disabilityStatus": self.disabilityStatus,
        "resumeUrl": self.resumeUrl}


class User(db.Model):
    password = db.Column(db.String, nullable=False)
    email = db.Column(db.String, db.ForeignKey(Profile.__table__.c.emailId), primary_key=True, nullable=False,
                      unique=True)
    def serialize(self):
        return {"password": self.password,
                "email": self.email}


class Jobs(db.Model):
    referenceId = db.Column(db.Integer, primary_key=True, nullable=False,unique=True)
    emailId = db.Column(db.String, db.ForeignKey(Profile.__table__.c.emailId), nullable=False)
    companyName = db.Column(db.String, nullable=False)
    jobtitle = db.Column(db.String, nullable=False)
    jobId = db.Column(db.String, nullable=True)
    status = db.Column(db.String, nullable=False)
    dateInserted = db.Column(db.String, nullable=False)

    def serialize(self):
        return{"emailId": self.emailId,
        "company": self.companyName,
        "jobTitle": self.jobtitle,
        "jobId": self.jobId,
        "status": self.status,
        "dateInserted": self.dateInserted
        }


def checkUser(email):

    # checking if user already exists
    user = User.query.filter_by(email=email).first()
    
    if not user:
        responseObject = {
            'status': 'fail',
            'message': 'User does not exists !!'
        }

        return responseObject

    else:
        print(user)
        print(user.serialize())
        responseObject = {
            'status': 'success',
            'data': user.serialize(),
            'message': 'User is present!'
        }

        return responseObject


def registerUser(fn, ln, phone, email, password, canWork, needSponsorship, resumeUrl, lUrl ="", tUrl="", gUrl="", pUrl="", oUrl="", age="", ethnicity="", gender="",
                 vStatus="", disStatus=""):
    user = User.query.filter_by(email=email).first()

    if not user:
        try:

            registerUser = Profile(
                firstName=fn,
                lastName=ln,
                phone=phone,                
                emailId=email,
                password = password,
                linkedInUrl=lUrl,
                twitterUrl=tUrl,
                githubUrl=gUrl,
                portfolioUrl=pUrl,
                otherUrl=oUrl,
                canLegallyWorkWithoutSponsorship=canWork,
                needSponsorshipInFuture=needSponsorship,
                ageRange=age,
                ethnicity=ethnicity,
                gender=gender,
                veteranStatus=vStatus,
                disabilityStatus =disStatus,
                resumeUrl = resumeUrl

            )

            db.session.add(registerUser)
            db.session.commit()
            # time.sleep(3)

            loginUser = User(
                email=email,
                password=password
            )

            db.session.add(loginUser)
            db.session.commit()

            responseObject = {
                'status': 'success',
                'message': 'Sucessfully registered.'
            }

            return responseObject

        except:
            e = sys.exc_info()
            responseObject = {
                'status': 'fail',
                'message': str(e)
            }
            return responseObject
    else:
        # if user already exists then send status as fail
        responseObject = {
            'status': 'fail',
            'message': 'User already exists. Please login!'
        }

        return responseObject


def jobApplied(email, companyName, jobTitle, status, dateInserted, jobId=""):
    jobs = Jobs.query.filter_by(emailId=email).filter_by(companyName=companyName).filter_by(jobtitle=jobTitle).all()

    if not jobs:
        try:
            job = Jobs(
                emailId=email,
                companyName=companyName,
                jobtitle=jobTitle,
                jobId =jobId,
                status=status,
                dateInserted=dateInserted
            )

            db.session.add(job)
            db.session.commit()
            # response
            responseObject = {
                'status': 'success',
                'message': 'Sucessfully added.'
            }

            return responseObject
        except:
            e = sys.exc_info()
            responseObject = {
                'status': 'fail',
                'message': str(e)
            }
            return responseObject

    else:
        responseObject = {
            'status': 'fail',
            'message': 'You have already applied to this job'
        }

        return responseObject


def updateJobStatus(jobChanged):

    
    jobs = Jobs.query.filter_by(emailId=jobChanged.emailId).filter_by(companyName=jobChanged.companyName).one()
    if jobs:
        try:

            db.session.query(Jobs).filter(Jobs.emailId == jobChanged.emailId).filter(Jobs.companyName == jobChanged.companyName).update({'status': jobChanged.status })
            db.session.commit()
            # response
            responseObject = {
                'status': 'success',
                'message': 'Sucessfully updated.'
            }

            return responseObject
        except:
            responseObject = {
                'status': 'fail',
                'message': 'Some error occured !!'
            }
            return responseObject

    else:
        responseObject = {
            'status': 'fail',
            'message': 'You have not applied to this job'
        }

        return responseObject


def getAllJobsByEmail(email):
    jobs = Jobs.query.filter_by(emailId=email).all()

    if not jobs:
        responseObject = {
            'status': 'fail',
            'message': 'You have not applied to any jobs'
        }

        return responseObject
    else:
        i=0
        final_json = {}
        for job in jobs:
            final_json[i]=job.serialize()
            i+=1

        responseObject = {
            'status': 'success',
            'data': final_json,
            'message': 'List of all jobs applied'

        }
        return responseObject


def getAllJobsByEmailAndStatus(emailId, status):
    jobs = Jobs.query.filter_by(emailId=emailId).filter_by(status=status).all()
    print("jobs inside getAllJobsByEmailAndStatus ")
    print(jobs)

    if not jobs:
        responseObject = {
            'status': 'fail',
            'data': 'No jobs applied',
            'message': 'You have not applied to any jobs'
        }

        return responseObject
    else:
        i=0
        final_json = {}
        for job in jobs:
            final_json[i]=job.serialize()
            i+=1

        responseObject = {
            'status': 'success',
            'data': final_json,
            'message': 'List of all jobs applied'

        }
        return responseObject

def getAllJobsByEmailAndStatusForGmail(emailId, status):
    jobs = Jobs.query.filter_by(emailId=emailId).filter_by(status=status).all()

    if not jobs:

        return []
    else:
        
        return jobs


def updateProfile(email, password, fn, ln, phone, lUrl, gUrl, tUrl, oUrl, canWork, needSponsorship, ethnicity, gender,
                  vStatus):
    user = Profile.query.filter_by(email=email).first()

    if user:
        try:
            # creating Users object
            updateUser = Profile(
                emailId=email,
                firstName=fn,
                lastName=ln,
                phone=phone,
                linkedInUrl=lUrl,
                githubUrl=gUrl,
                twitterUrl=tUrl,
                otherUrl=oUrl,
                CanLegallyWorkWithoutSponsorship=canWork,
                needSponsorshipInFuture=needSponsorship,
                ethnicity=ethnicity,
                gender=gender,
                veteranStatus=vStatus,
                resume = resumeUrl

            )
            db.session.add(updateUser)
            db.session.commit()
            # response
            responseObject = {
                'status': 'success',
                'message': 'Sucessfully updated.'
            }

            return responseObject

        except:
            responseObject = {
                'status': 'fail',
                'message': 'Some error occured !!'
            }
            return responseObject

    else:
        responseObject = {
            'status': 'fail',
            'message': 'User does not exist !!'
        }
        return responseObject


def getProfileByEmail(email):
    user = Profile.query.filter_by(email=email).first()
    if not user:
        responseObject = {
            'status': 'fail',
            'message': 'User does not exist !!'
        }
        return responseObject
    else:
        responseObject = {
            'status': 'success',
            'data': user.serialize(),
            'message': 'User is found.'
        }

        return responseObject

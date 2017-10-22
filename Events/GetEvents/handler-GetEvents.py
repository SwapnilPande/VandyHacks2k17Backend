import sys
import os
import datetime

here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "../vendored"))

import database
import events

dbName = os.environ['dbname'] #name of the postgres database to connect to
dbUser = os.environ['dbuser'] #name of the database user to use
dbHost = os.environ['dbhost'] #database host to connect to
dbPassword = os.environ['dbpassword'] #password of the database to connect to

#Database object
db = database.DatabaseConnection(dbName, dbUser, dbHost, dbPassword)

def handler(event, context):
	time = datetime.datetime.now() - datetime.timedelta(hours=1)
	userID = None
	eventType = None
	eventScale = None

	if('userID' in event):
		userID = event['userID']
		return events.getMyEvents(db, userID, time)

	if('eventType' in event):
		eventType = event['eventType']

	if('eventScale' in event):
		eventScale = event['eventScale']

    #Call and return createUser
	return events.getEvents(db, eventType, eventScale, time)

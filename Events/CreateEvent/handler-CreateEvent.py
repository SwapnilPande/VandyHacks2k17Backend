import sys
import os

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
    #Call and return createUser
    return events.createEvent(db, event['scale'], event['type'], event['startTime'], event['length']) 

import sys
import os

here = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(here, "../vendored"))

import database
import events

dbName = 'vhsocialrun'#os.environ['dbname'] #name of the postgres database to connect to
dbUser = 'swapnofshin'#os.environ['dbuser'] #name of the database user to use
dbHost = 'vhsocialrun.culrclwoj6ec.us-east-1.rds.amazonaws.com'#os.environ['dbhost'] #database host to connect to
dbPassword = 'password'#os.environ['dbpassword'] #password of the database to connect to

#Database object
db = database.DatabaseConnection(dbName, dbUser, dbHost, dbPassword)

def handler(event, context):
    #Call and return createUser
    return events.updateProgress(db, event['userID'], event['lat'], event['lon']) 
import datetime


############################################################################
# timePgToClient(date)
# Converts time format that PostGres returns into correct format for client application
# Parameters: date - datetime object
#Returns: string with date in format: YYYYMMDDHHMM
def timePgToClient(date):
	year = str(date.year)
	month = str(date.month)
	day = str(date.day)
	hour = str(date.hour)
	minute = str(date.minute)
	if (len(month) < 2):
		month = "0" + month
	if (len(day) < 2):
		day = "0" + day
	if (len(hour) < 2):
		hour = "0" + hour
	if (len(minute) < 2):
		minute = "0" + minute

	return (year + month + day + hour + minute)

############################################################################
# timeClientToPg(date)
# Converts time format that the client returns into correct format for Postgres
# Parameters: date - string object containing time in format YYYYMMDDHHMM
#Returns: string with date in format: YYYY-MM-DD HH:MM:SS
def timeClientToPg(date):
    return (date[:4] + "-" + date[4:6] + "-" + date[6:8] +
            " " + date[8:10] +  ":" + date[10:] + ":00")



def createEvent(db, scale, eventType, startTime, length):
	inputs = {}
	if(eventType == 0):
		queryString = """
		INSERT INTO events (event_scale, event_type, start_time, length_time) 
		VALUES (%(scale)s, %(eventType)s, %(startTime)s, %(endTime)s) 
		RETURNING event_id;"""
		inputs = { 'scale' : scale, 
		'eventType' : eventType, 
		'startTime' : timeClientToPg(startTime), 
		'endTime' : timeClientToPg(length) 
		}

	else:
		inputs = { 'scale' : scale, 'eventType' : eventType, 'startTime' : timeClientToPg(startTime), 'length' : length }
		queryString = """INSERT INTO events (event_scale, event_type, start_time, length_distance) VALUES (%(scale)s, %(eventType)s, %(startTime)s, %(length)s) RETURNING event_id;"""
	
	output = db.dbExecuteReturnOne(queryString, inputs)
	if(output):
		return {'eventID' : output[0]}
	return {'eventID' : ''}

def joinEvent(db, userID, eventID):
	queryString = """
		SELECT event_type 
		FROM events
		WHERE event_id = %(eventID)s 
		LIMIT 1;"""
	inputs = {
		'eventID' : int(eventID),
		'userID' : int(userID)
	}
	output = db.dbExecuteReturnOne(queryString, inputs)

	#Making sure we got real data
	if(not output):
		return {}

	queryString2 = ""

	if(output[0] == 1):
		queryString2 = """
			INSERT INTO user_event_progress (event_id, user_id, progress)
			VALUES (%(eventID)s, %(userID)s, 0);"""
	else:
		queryString2 = """
			INSERT INTO user_event_progress (event_id, user_id)
			VALUES (%(eventID)s, %(userID)s);"""

	db.dbExecuteReturnNone(queryString2, inputs)

	return "Success"




def updateProgress(db, userID, lat, lon):
	#Getting current progress for all distance events for a user
	queryString = """
	SELECT uid FROM user_event_progress
	WHERE user_id = %(userID)s AND progress IS NOT NULL;
	"""
	inputs = {
		'userID' : int(userID)
	}
	output = db.dbExecuteReturnAll(queryString, inputs)
	outList = []
	for uid in output:
		outList.append(uid[0])
	
	queryLoc = """
		SELECT loc FROM user_loc 
		WHERE user_id = %(userID)s 
		LIMIT 1;"""
	inputLoc= { 'userID' : userID }
	locOut = db.dbExecuteReturnOne(queryLoc, inputLoc)
	userLoc = locOut[0]

	queryStringProgress = """
	UPDATE user_event_progress
	SET progress = progress + ST_DISTANCE(%(userLoc)s::geography, st_setsrid(st_makepoint(%(lon)s,%(lat)s),4326)::geography)
	WHERE uid IN ("""  + ','.join(str(uid) for uid in outList) + ")"

	inputsProgress = {
		'lat' : lat,
		'lon' : lon,
		'userLoc' : userLoc
	}

	output = db.dbExecuteReturnNone(queryStringProgress, inputsProgress)

	queryStringUpdateLoc = """
	UPDATE user_loc
	SET loc = ST_SetSRID(ST_MakePoint(%(lon)s,%(lat)s), 4326)
	WHERE user_id = %(userID)s;"""

	inputsUpdateLoc = {
		'lat' : lat,
		'lon' : lon,
		'userID' : userID
	}

	db.dbExecuteReturnNone(queryStringUpdateLoc, inputsUpdateLoc)


	return "Success"



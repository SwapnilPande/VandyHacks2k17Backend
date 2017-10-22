import datetime
import sms


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

def getDatetime(date):
	return datetime.datetime(year=int(date[:4]),month=int(date[4:6]),day=int(date[6:8]),
		hour=int(date[8:10]), minute=int(date[10:]))



def createEvent(db, scale, eventType, startTime, length, lat, lon, name):
	

	inputs = {}
	if(eventType == 0):
		dTime = datetime.timedelta(minutes = int(length)) #Time delta between start and finish
		timeLength = getDatetime(startTime) + dTime
		queryString = """
		INSERT INTO events (event_scale, event_type, start_time, length_time, loc, name) 
		VALUES (%(scale)s, %(eventType)s, %(startTime)s, %(timeLength)s, 
				ST_SetSRID(ST_MakePoint(%(lon)s,%(lat)s), 4326), %(name)s) 
		RETURNING event_id;"""
		inputs = { 'scale' : scale, 
		'eventType' : eventType, 
		'startTime' : timeClientToPg(startTime), 
		'timeLength' : timeLength,
		'lat' : lat,
		'lon' : lon,
		'name' : name
		}

	else:
		inputs = { 'scale' : scale, 'eventType' : eventType, 'startTime' : timeClientToPg(startTime), 'length' : length , 'lat' : lat, 'lon': lon, 'name' : name}
		queryString = """INSERT INTO events (event_scale, event_type, start_time, length_distance, loc, name) VALUES (%(scale)s, %(eventType)s, %(startTime)s, %(length)s, ST_SetSRID(ST_MakePoint(%(lon)s,%(lat)s), 4326), %(name)s) RETURNING event_id;"""
	
	output = db.dbExecuteReturnOne(queryString, inputs)
	if(output):
		return {'eventID' : output[0]}
	return {'eventID' : ''}



def joinEvent(db, userID, eventID):
	queryString = """
			INSERT INTO user_event_progress (event_id, user_id, progress)
			VALUES (%(eventID)s, %(userID)s, 0);"""
	inputs = {
		'eventID' : int(eventID),
		'userID' : int(userID)
	}

	db.dbExecuteReturnNone(queryString, inputs)

	return "Success"




def updateProgress(db, userID, lat, lon):
	#Getting current progress for all active events for a user
	queryString = """
	SELECT uid FROM user_event_progress
	WHERE event_state = 1 AND user_id = %(userID)s;
	"""
	inputs = {
		'userID' : int(userID)
	}
	output = db.dbExecuteReturnAll(queryString, inputs)
	if(not output):
		return {'distance' : 0}
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
	WHERE uid IN ("""  + ','.join(str(uid) for uid in outList) + """)
	RETURNING progress;"""

	inputsProgress = {
		'lat' : lat,
		'lon' : lon,
		'userLoc' : userLoc
	}

	output = db.dbExecuteReturnOne(queryStringProgress, inputsProgress)
	

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


	return {
		'distance' : output[0]
	}


def getMyEvents(db, userID, curTime):
	queryString = """
		SELECT user_event_progress.event_id,
				events.event_scale, 
				events.event_type,
				events.start_time,
				events.length_time,
				events.length_distance,
				events.name
		FROM user_event_progress
		INNER JOIN events 
		ON user_event_progress.event_id = events.event_id
		WHERE user_event_progress.user_id = %(userID)s;"""
	inputs = {
		'userID' : userID
	}

	output = db.dbExecuteReturnAll(queryString, inputs)
	outList = []
	#Reformatting data for JSON output
	for e in output:
		if(e[2] == 0):
			outList.append( {
				'eventID' : e[0],
				'eventScale' : e[1],
				'eventType' : e[2],
				'startTime' : timePgToClient(e[3]),
				'length' : ((curTime - e[4]).total_seconds())/60.0,
				'name': e[6]
				})
		else:
			outList.append( {
				'eventID' : e[0],
				'eventScale' : e[1],
				'eventType' : e[2],
				'startTime' : timePgToClient(e[3]),
				'length' : e[5],
				'name': e[6]
				})
	return outList

def getEvents(db, eventType, eventScale, curTime):
	queryString = """
	SELECT event_id,
			event_scale, 
			event_type,
			start_time,
			length_time,
			length_distance,
			name
	FROM events 
	"""
	typeBool = eventType is not None
	scaleBool = eventScale is not None
	if(typeBool or scaleBool):
		queryString += "WHERE "
		if(typeBool):
			queryString += "events.event_type = %(eventType)s "
		if(typeBool and scaleBool):
			queryString += "AND "
		if(scaleBool):
			queryString += "events.event_scale = %(eventScale)s;"
	inputs = {
		'eventType' : eventType,
		'eventScale' : eventScale
	}
	output = db.dbExecuteReturnAll(queryString, inputs)
	outList = []
	#Reformatting data for JSON output
	for e in output:
		if(e[2] == 0):
			outList.append( {
				'eventID' : e[0],
				'eventScale' : e[1],
				'eventType' : e[2],
				'startTime' : timePgToClient(e[3]),
				'length' : ((curTime - e[4]).total_seconds())/60.0,
				'name': e[6]
				})
		else:
			outList.append( {
				'eventID' : e[0],
				'eventScale' : e[1],
				'eventType' : e[2],
				'startTime' : timePgToClient(e[3]),
				'length' : e[5],
				'name': e[6]
				})
	return {
		'items' : outList
	}

#Returns the numbers of all users who are participating in event
def getNumbers(db, eventID):
	queryString = """
	SELECT users.phone FROM user_event_progress
	INNER JOIN users ON user_event_progress.user_id = users.user_id
	WHERE user_event_progress.event_id = %(eventID)s"""
	inputs = {
		'eventID' : eventID
	}
	output = db.dbExecuteReturnAll(queryString, inputs)
	outList = []
	for phone in output:
		outList.append(phone[0])
	return outList

def getMessage(db, eventID):
	queryString = """
	SELECT event_type FROM events
	WHERE event_id = %(eventID)s;"""
	inputs = {
		'eventID': eventID
	}
	eventType = db.dbExecuteReturnOne(queryString, inputs)[0]
	if(eventType == 0):
		queryString2 = """
		SELECT EXTRACT(EPOCH FROM length_time - start_time)/60
		FROM events
		WHERE event_id = %(eventID)s;"""
		inputs2 = {
			'eventID': eventID
		} 
		minutes = db.dbExecuteReturnOne(queryString2, inputs2)[0]
		return "You're " + str(minutes) + " minute run is beginning now!"
	else:
		queryString2 = """
		SELECT length_distance
		FROM events
		WHERE event_id = %(eventID)s;"""
		inputs2 = {
			'eventID': eventID
		} 
		distance = db.dbExecuteReturnOne(queryString2, inputs2)[0]
		return "Your " + str(distance) + "km run is beginning now!"


def setStateToOne(db, eventID):
	queryString = """
	UPDATE user_event_progress
	SET event_state = 1
	WHERE event_id = %(eventID)s;"""
	inputs = {
		'eventID': eventID
	}
	db.dbExecuteReturnNone(queryString, inputs)

def startEvents(db, curTime):
	queryString = """
	SELECT events.event_id FROM events
	INNER JOIN user_event_progress
	ON events.event_id = user_event_progress.event_id
	WHERE event_state = 0 AND 
	EXTRACT(EPOCH FROM start_time - TIMESTAMP %(pgTime)s)/60 < 1;"""

	inputs = {
		"pgTime" : curTime
	}

	#Returns all of the events that need to start
	output = db.dbExecuteReturnAll(queryString, inputs)
	numbers = []

	for eventID in output: 
		numbers = getNumbers(db, eventID[0])
		sms.sendMessages(numbers, getMessage(db, eventID[0]))
		setStateToOne(db, eventID)

def updateLastRunStats(db, userID, distance, time, speed, rank):
	queryString = """
	UPDATE last_run_stats
	SET time = %(time)s,
		distance = %(distance)s,
		speed = %(speed)s,
		rank = %(rank)s
	WHERE user_id = %(userID)s;	"""
	inputs = {
		'time' : time,
		'distance' : distance,
		'speed' : speed,
		'rank' : rank,
		'userID' : userID
	}
	db.dbExecuteReturnNone(queryString, inputs)

def updateStoredStats(db, userID, distance, time, rank):
	raceWon = 0
	if (rank == 1):
		raceWon = 1
	queryString = """
	UPDATE users
	SET number_races = number_races + 1,
		number_won = number_won + %(raceWon)s,
		total_distance = total_distance + %(distance)s,
		total_time = total_time + %(time)s
	WHERE user_id = %(userID)s;	"""
	inputs = {
		'time' : time,
		'distance' : distance,
		'rank' : rank,
		'userID' : userID,
		'raceWon' : raceWon
	}
	db.dbExecuteReturnNone(queryString, inputs)


def endEvents(db, curTime):
	queryString = """
		SELECT user_event_progress.event_id,
				user_event_progress.user_id,
				user_event_progress.progress,
				events.start_time 
		FROM user_event_progress
		INNER JOIN events 
		ON user_event_progress.event_id = events.event_id
		WHERE user_event_progress.event_state = 1 
			AND events.event_type = 1 
			AND user_event_progress.progress >= events.length_distance;"""
	output = db.dbExecuteReturnAll(queryString)

	queryString = """
		SELECT user_event_progress.event_id,
				user_event_progress.user_id,
				user_event_progress.progress,
				events.start_time 
		FROM user_event_progress
		INNER JOIN events 
		ON user_event_progress.event_id = events.event_id
		WHERE events.event_type = 0 
			AND %(curTime)s >= events.length_time;"""
	inputs = {
		"curTime" : curTime
	}

	output = output + db.dbExecuteReturnAll(queryString, inputs)
	for user in output:
		distance = user[2]
		time = curTime - user[3]
		hours = (time.total_seconds()/3600.0)
		speed = float(distance)/hours
		queryStringRanking = """
		UPDATE user_event_progress
		SET event_state = 2
		WHERE user_id = %(userID)s AND event_id = %(eventID)s;
		SELECT COUNT(event_state)
		FROM user_event_progress
		WHERE event_id = %(eventID)s
		GROUP BY event_id;"""

		inputs = {
			'userID' : user[1],
			'eventID' : user[0]
		}
		rank = db.dbExecuteReturnOne(queryStringRanking, inputs)[0]

		updateLastRunStats(db, user[1], distance, hours, speed, rank)
		updateStoredStats(db,user[1],distance,hours,rank)

		queryStringDeletion = """
			SELECT uid FROM user_event_progress
			WHERE event_state != 2 AND event_id = %(eventID)s;"""
		inputsDeletion = {
			'eventID' : user[0]
		}
		outputDeletion = db.dbExecuteReturnOne(queryStringDeletion, inputsDeletion)
		if(not outputDeletion):
			queryStringDelete = """
			DELETE FROM events
			WHERE event_id = %(eventID)s;
			DELETE FROM user_event_progress
			WHERE event_id = %(eventID)s;"""
			db.dbExecuteReturnNone(queryStringDelete, inputsDeletion)

def getProgress(db, userID):
	queryString ="""
	SELECT users.name, user_event_progress.progress
	FROM user_event_progress
	INNER JOIN users
	ON user_event_progress.user_id = users.user_id
	WHERE user_event_progress.user_id != %(userID)s
	LIMIT 1;"""
	inputs = {
		'userID' : userID
	}
	output = db.dbExecuteReturnOne(queryString, inputs)
	return {
		'name' : output[0],
		'progress' : output[1]
	}

def getCurrentEvents(db, userID):
	queryString = """
	SELECT events.length_time FROM events
	INNER JOIN user_event_progress
	ON events.event_id = user_event_progress.event_id
	WHERE user_event_progress.progress = 1 
		AND user_event_progress.user_id = %(userID)s;"""
	inputs = {
		"userID" : userID
	}
	output = db.dbExecuteReturnOne(queryString, inputs)
	if(output):
		return {"length" : output[0]}
	return {}











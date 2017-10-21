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
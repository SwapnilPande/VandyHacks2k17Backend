

def createUser(db, name, email, lat, lon):
	queryString = """
        INSERT INTO users (name, email) 
        VALUES (%(name)s, %(email)s) 
        RETURNING user_id;"""

	inputs = {'name' : name, 'email' : email}
	output = db.dbExecuteReturnOne(queryString, inputs)
	if(output):
		uid = output[0]
		queryString2 = """
		INSERT INTO user_loc (user_id, loc) 
        VALUES (%(userID)s, ST_SetSRID(ST_MakePoint(%(lon)s,%(lat)s), 4326));"""
		inputs2 = { 'userID': uid, 'lat' : lat, 'lon' : lon}
		db.dbExecuteReturnNone(queryString2, inputs2)
        return {'UID' : uid}
	return {'UID' : ''}


def signInUser(db, email, lat, lon):
	queryString = """
        SELECT * FROM users
        WHERE email=%(email)s
        LIMIT 1;"""

	inputs = {'email' : email}
	output = db.dbExecuteReturnOne(queryString, inputs)
	if(output):
		#Updating the user location here
		uid = output[0]
		queryString2 = """
		UPDATE user_loc
        SET loc = ST_SetSRID(ST_MakePoint(%(lon)s,%(lat)s), 4326)
        WHERE userID = %(userID)s;"""
		inputs2 = { 'userID': uid, 'lat' : lat, 'lon' : lon}
		return {'UID' : output[0]}
	return {'UID' : ''}

def getUserInfo(db, uid):
	queryString = """
        SELECT (name, email, ranking, number_races, number_won, 
        		total_distance, total_time) 
        FROM users
        WHERE user_id=%(uid)s
        LIMIT 1;"""

	inputs = {'uid' : uid}
	output = db.dbExecuteReturnOne(queryString, inputs)
	if(output):
		output = output[0][1:-1].split(',')
		return {
			"name" : output[0][1:-1],
			"email" : output[1],
			"ranking" : output[2],
			"number_races" : output[3],
			"number_won" : output[4],
			"total_distance" : output[5],
			"total_time" : output[6]
		}
	return {'UID' : ''}




  

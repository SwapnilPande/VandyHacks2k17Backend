

def createUser(db, name, email):
	queryString = """
        INSERT INTO users (name, email) 
        VALUES (%(name)s, %(email)s) 
        RETURNING user_id;"""

	inputs = {'name' : name, 'email' : email}
	output = db.dbExecuteReturnOne(queryString, inputs)
	if(output):
		return {'UID' : output[0]}
	return {'UID' : ''}


def signInUser(db, email):
	queryString = """
        SELECT * FROM users
        WHERE email=%(email)s
        LIMIT 1;"""

	inputs = {'email' : email}
	output = db.dbExecuteReturnOne(queryString, inputs)
	if(output):
		return {'UID' : output[0]}
	return {'UID' : ''}



  

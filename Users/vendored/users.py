

def createUser(db, name, email):
	queryString = """
        INSERT INTO users (name, email) 
        VALUES (%(name)s, %(email)s) 
        RETURNING user_id;"""

	inputs = {'name' : name, 'email' : email}
	output = db.dbExecuteReturnOne(queryString, inputs)
	return {'UID' : output[0]}


  

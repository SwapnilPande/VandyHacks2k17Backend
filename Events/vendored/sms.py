import boto3

client = boto3.client('sns')

def sendMessage(number, message):
    client.publish(
    PhoneNumber = number, 
    Message = message)


def sendMessages(numbers, message):
	for number in numbers:
		sendMessage(number,message)

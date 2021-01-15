import json
import boto3
import logging
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    otp = event['otp']
    validVisitor = check_otp(otp)
    visitorInfo = None
    if validVisitor:
        visitorInfo = retrieve_info(validVisitor['faceId'])
        message = 'Welcome to the house '
        delete_otp(otp)
    else:    
        message = 'Permission Denied'
        
    if visitorInfo:
        message += visitorInfo['name'] + '! Your entry has been authorized.'
    return {
        'statusCode': 200,
        'body': json.dumps(message)
    }


# Check whether OTP is valid
def check_otp(otp):
    table = dynamodb.Table('hw2-db1-passcode')
    response = table.query(
        KeyConditionExpression=Key('otp').eq(otp)
    )
    print('CHECK OTP RESPONSE')
    print(response)
    if response['Count']>0:
        return response['Items'][0]
    return None
        

# Delete used OTP
def delete_otp(otp):
    table = dynamodb.Table('hw2-db1-passcode')
    response = table.delete_item(
        Key={
            'otp': otp
        }
    )
    print('DELETE OTP RESPONSE')
    print(response)


# Retrieve Visitor info for personalized message
def retrieve_info(faceId):
    table = dynamodb.Table('hw2-db2-visitor')
    response = table.query(
        KeyConditionExpression=Key('faceId').eq(faceId)
    )
    print('RETRIEVE VISITOR RESPONSE')
    if response['Count']>0:
        return response['Items'][0]
    return None
    
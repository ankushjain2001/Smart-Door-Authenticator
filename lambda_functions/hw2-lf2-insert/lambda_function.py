import json
import time
import boto3
import logging
from random import randint

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
rek = boto3.client('rekognition')
sns = boto3.client('sns')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    name = event['name']
    phoneNumber = event['phone']
    imageId = event['faceId']
    if imageId != "":
        response = rek.index_faces(
            CollectionId='hw2collection',
            Image={
                'S3Object': {
                    'Bucket': 'hw2-b1-photostore',
                    'Name': imageId
                }
            },
            ExternalImageId = name.replace(" ", ""),
            DetectionAttributes = [
                'DEFAULT',
            ],
            MaxFaces=1,
            QualityFilter='AUTO'
        )
        faceId = (((response['FaceRecords'])[0])['Face'])['FaceId']
        print('FACE ID: ', faceId)
        print('IMAGE ID: ', imageId)
        insert_visitor(faceId, name, phoneNumber, imageId)
        
        otp = randint(100000, 999999)
        print('OTP: ', otp)
        insert_otp(faceId, otp)
        sms_visitor(phoneNumber, str(otp))
        
        return {
            'statusCode': 200,
            'body': json.dumps('OTP has been sent to the visitor.')
        }
    else:
        sms_visitor(phoneNumber, "")
        return {
            'statusCode': 200,
            'body': json.dumps('Visitor has been denied entry.')
        }
    

# Insert new visitor after approval
def insert_visitor(faceId, name, phoneNumber, imageId):
    table = dynamodb.Table('hw2-db2-visitor')
    result = table.put_item(
        Item = {
                'faceId': faceId,
                'name': name,
                'phoneNumber': phoneNumber,
                'photos': [
                    {
                        'objectKey': imageId,
                        'bucket': 'hw2-b1-photostore',
                        'createdTimestamp':time.strftime("%Y%m%d-%H%M%S")
                    }    
                ]

        })
    logger.info(name + ' with ' + faceId + ' inserted to visitors table')
    return result


# Insert otp for the newly verified user
def insert_otp(faceId, otp):
    table = dynamodb.Table('hw2-db1-passcode')
    result = table.put_item(
        Item = {
                'otp': str(otp),
                'faceId':faceId,
                'current_time':int(time.time()),
                'expiration_time':int(time.time() + 300)

        })


# SMS Visitor for acceptance or denial of entry
def sms_visitor(phoneNumber, otp):
    url = 'http://cc-hw2-visitorportal.s3-website-us-east-1.amazonaws.com/'
    if otp != "":
        message = 'Your Smart Door verification code is ' + otp + '.\n\nThe code is valid for 5 minutes.\n\nEnter here '+ url
    else:
        message = 'Sorry, the owner has denied your request to enter.' 
    sns.publish(
        PhoneNumber = '+1'+str(phoneNumber),
        Message = message
    )

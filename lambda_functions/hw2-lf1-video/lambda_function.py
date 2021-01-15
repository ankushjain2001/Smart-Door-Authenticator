import cv2
import json
import time
import boto3
import base64
import logging
from boto3.dynamodb.conditions import Key
from random import randint

s3 = boto3.client('s3')
sns = boto3.client('sns')
ses = boto3.client('ses')
dynamodb = boto3.resource('dynamodb')
kinesis = boto3.client('kinesis-video-media', 
                       endpoint_url='https://s-f10ab6ea.kinesisvideo.us-east-1.amazonaws.com', 
                       region_name='us-east-1'
                       )

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    record = event['Records'][0]
    # print('RECORD: ', record)
    decoded_record = base64.b64decode(record["kinesis"]["data"])
    # print('DECODED RECORD: ', decoded_record)
    decoded_record = json.loads(decoded_record.decode('utf-8'))
    print('UTF DECODED RECORD: ', decoded_record)
    faces = decoded_record["FaceSearchResponse"]
    print('FACES: ', faces)
    
    img_prefix='img_'
    faceId = ''
    
    if len(faces) != 0:
        for f in faces:
            if len(f['MatchedFaces']) != 0: # INVERT ME
                print('MATCHING FACE FOUND')
                # There can be mutiple matched faces for a single face.
                # We pick the top most match (since )
                for matchedFace in f["MatchedFaces"]:
                    mf = matchedFace["Face"]
                    faceId = mf["FaceId"]

            else:
                print('NON MATCHING FACE FOUND')
                # Get stream
                if 'InputInformation' in decoded_record:
                    frag = decoded_record["InputInformation"]["KinesisVideo"]["FragmentNumber"]
                    print('Fragment Number: ', frag)
                    stream = kinesis.get_media(
                        StreamARN='arn:aws:kinesisvideo:us-east-1:450113335315:stream/hw2-kvs1/1604798395984',
                        StartSelector={
                            'StartSelectorType': 'FRAGMENT_NUMBER',
                            'AfterFragmentNumber': frag
                        }
                    )
                    print('STREAM: ', stream)   

                    # Extract image from video and save to bucket                    
                    with open('/tmp/stream.mp4', 'wb') as f:
                        body = stream['Payload'].read(1024*30)
                        print('BODY')
                        print(body)
                        f.write(body)
                        
                    # Capture video
                    vcap = cv2.VideoCapture('/tmp/stream.mp4')
                    ret, frame = vcap.read()
                    if frame is not None:
                        # Display the resulting frame
                        vcap.set(1, int(vcap.get(cv2.CAP_PROP_FRAME_COUNT)/2)-1)
                        img_prefix = img_prefix + time.strftime("%Y%m%d-%H%M%S") + '.jpg'
                        cv2.imwrite('/tmp/' + img_prefix, frame)
                        # Upload to S3
                        s3.upload_file('/tmp/' + img_prefix, 'hw2-b1-photostore', img_prefix)
                        s3.upload_file('/tmp/' + img_prefix, 'cc-hw2-ownerportal', 'img/' + img_prefix)
                        print('Final key frame uploaded to S3')
                        vcap.release()
                        print('Uploaded Image Name :', img_prefix)
                        break
                    else:
                        print("No frames found")
                        break
        
        # If EXISTING USER
        print('MATCHED faceId: ', faceId)
        if faceId != '':
            visitor = verify_visitor(faceId)
            print('VISITOR: ', visitor)
            if visitor:
                otp = randint(100000, 999999)
                update_visitor(visitor, faceId, img_prefix)
                insert_otp(faceId, otp)
                phoneNumber = visitor['phoneNumber']
                sms_visitor(phoneNumber, str(otp))
        # Else NEW USER
        else:
            print('Final Key: ', img_prefix)
            sms_owner(img_prefix)
        # Return for FACES
        return {
            'statusCode': 200,
            'body': json.dumps('Successful Request')
        }
        

    else:
        print('NO FACES IN CAMERA')
        

# Verify the visitor
def verify_visitor(faceId):
    table = dynamodb.Table('hw2-db2-visitor')
    response = table.query(
        KeyConditionExpression = Key('faceId').eq(faceId)
    )
    if response['Count']>0:
        print('VERIFICATION RESPONSE: ', response)
        return response['Items'][0]
    return None
        

# Update the visitor photo if existing
def update_visitor(visitor, faceId, photo):
    table = dynamodb.Table('hw2-db2-visitor')
    visitor_photos = visitor['photos']
    photos = {
                'objectKey': photo,
                'bucket': 'hw2-b1-photostore',
                'createdTimestamp':time.strftime("%Y%m%d-%H%M%S")
            }
    print('VISITOR PHOTO UPDATED ', photos)
    visitor_photos.append(photos)
    table.delete_item(
        Key = {
            'faceId' : faceId
        }
    )
    table.put_item(
        Item = {
                'faceId': faceId,
                'name':visitor['name'],
                'phoneNumber': visitor['phoneNumber'],
                'photos': visitor_photos
        })


# Insert OTP to the passcode table
def insert_otp(faceId, otp):
    table = dynamodb.Table('hw2-db1-passcode')
    print('OTP EXPIRATION: ', int(int(time.time())+300))
    table.put_item(
        Item = {
                'otp': str(otp),
                'faceId':faceId,
                'current_time':int(time.time()),
                'expiration_time':int(time.time() + 300)
        })


# Send SMS to owner if new visitor
def sms_owner(img_prefix):
    owner_phone = '+19294202135' #'+12016735763'
    url = 'http://cc-hw2-ownerportal.s3-website-us-east-1.amazonaws.com/index.html?uid='+img_prefix
    message = 'Please give access or deny the request for the visitor by visiting '+ url 
    sns.publish(
        PhoneNumber = owner_phone,
        Message = message
    )
    print('SENT SMS TO OWNER', str(owner_phone))
    
    try:
        ses.send_email(
            Source='ankushjain2001@yahoo.co.in',
            Destination={
                'ToAddresses': [
                    'aj2885@nyu.edu',
                ]
            },
            Message={
                'Subject': {
                    'Data': 'Smart Door Alert: Review new visitor'
                },
                'Body': {
                    'Text': {
                        'Data': 'Hi,\n\nA new visitor has arrived at your door. Please review them. Image can be seen here. \n\n' + 'http://cc-hw2-ownerportal.s3.amazonaws.com/img/'+img_prefix + '\n\nThanks'
                    }
                }
            }
        )
        print('EMAIL SENT TO OWNER')
    except:
        print('ERROR OCCURED IN SENDING EMAIL')
    
    
# Send SMS to visitor if existing
def sms_visitor(phoneNumber, otp):
    url = 'http://cc-hw2-visitorportal.s3-website-us-east-1.amazonaws.com/index.html'
    phoneNumber = '+1'+phoneNumber
    message = 'Your Smart Door verification code is ' + otp + '.\n\nThe code is valid for 5 minutes.\n\nEnter here '+ url
    sns.publish(
        PhoneNumber = phoneNumber,
        Message = message
    )
    print('SENT SMS TO VISITOR',str(phoneNumber))

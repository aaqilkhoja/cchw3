import json
import urllib.parse
import boto3
import datetime
import requests

print('Loading function')

s3 = boto3.client('s3')
rek = boto3.client('rekognition')


def lambda_handler(event, context):
    # ES setup
    es_domain_endpoint = 'search-photos-hevt6ucrdsmqtfzihe4dtamqya.us-east-1.es.amazonaws.com'
    region = 'us-east-1'
    master_username = 'cc_hw3'
    master_password = 'cloud_HW3@mmaq'
    es_url = f'https://{es_domain_endpoint}/photos'

    # session for put and post requests to the elasticsearch server
    session = requests.Session()
    session.auth = (master_username, master_password)
    session.headers.update({'Content-Type': 'application/x-ndjson'})

    # Get the object from the event and show its content type
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    print(f"Received key: {key} for bucket: {bucket}")
    
    try:
        # Getting the image metadata
        metadata = s3.head_object(Bucket=bucket, Key=key)
        custom_labels = None
        
        if "Metadata" in metadata and "customlabels" in metadata["Metadata"]:
            custom_labels = metadata["Metadata"]["customlabels"].split(",")
        
        created_date = metadata['LastModified']
        created_date = created_date.strftime('%Y-%m-%dT%H:%M:%S')

        print(f"Creation date: {created_date}")
        print("Starting rekognition")
        labels = detect_labels(photo=key, bucket=bucket)
        print(f"Response labels from rekognition: {labels}")
        
        if custom_labels is not None:
            labels = labels + custom_labels
        
        response = {
            "objectKey": key,
            "bucket": bucket,
            "createdTimestamp": created_date,
            "labels": labels
        }
        print(f"Response from rekognition: {response}")

        obj_id = response['objectKey'].split('.')[:-1]
        obj_id = '.'.join(obj_id)

        response = session.post(es_url+f"/_doc/{obj_id}", data=json.dumps(response))
        print(f"Response from elasticsearch: {response}")
        
        if response.status_code // 100 == 2:
            return {
                'statusCode': response.status_code,
                'body': 'Document indexed successfully.'
            }
        else:
            return {
                'statusCode': response.status_code,
                'body': f'Error: {response.text}'
            }
        
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e


def detect_labels(photo, bucket):
    print("In detect labels")
    response = rek.detect_labels(Image={'S3Object':{'Bucket':bucket,'Name':photo}},MaxLabels=10,
    # Uncomment to use image properties and filtration settings
    #Features=["GENERAL_LABELS", "IMAGE_PROPERTIES"],
    #Settings={"GeneralLabels": {"LabelInclusionFilters":["Cat"]},
    # "ImageProperties": {"MaxDominantColors":10}}
    )
    
    print(f'Detected {len(response["Labels"])} labels for ' + photo)
    print()
    labels = []
    for label in response['Labels']:
        labels.append(label['Name'])
    
    return labels
              
 

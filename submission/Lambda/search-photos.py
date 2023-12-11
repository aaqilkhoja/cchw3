import boto3
import requests
import json
botId = 'XYVZ6XR2Q0'
botAliasId = 'TSTALIASID'
userId='id'
def get_data_es(labels):
    print("inside elastic seach. Labels: ", labels)
    # Replace 'your-es-domain-endpoint' with the actual endpoint of your Elasticsearch domain
    es_domain_endpoint = (
        "search-photos-hevt6ucrdsmqtfzihe4dtamqya.us-east-1.es.amazonaws.com"
    )

    # Replace 'your-master-username' and 'your-master-password' with your Elasticsearch master user credentials
    master_username = "cc_hw3"
    master_password = "cloud_HW3@mmaq"

    # Set up the Elasticsearch endpoint URL
    es_url = f"https://{es_domain_endpoint}/photos"

    # Create a requests session with AWS SigV4 authentication
    session = requests.Session()
    session.auth = (master_username, master_password)
    session.headers.update({"Content-Type": "application/x-ndjson"})

    # labels = ["Wood", "Cat", "helicopter"]
    responses = []
    img_data = {}
    for key in labels.keys():
        if labels[key] > 0:
            label = key
            query = {
                "query": {
                    # "labels":label
                    "fuzzy": {"labels": label}
                }
            }
            response = session.get(es_url + f"/_search", data=json.dumps(query))
            hits = response.json()["hits"]["hits"]
            print(f"Hits received: ", hits)
            
            for hit in hits:
                img_data[hit["_source"]["objectKey"]] = {"url":hit["_source"]["objectKey"],"labels":hit["_source"]["labels"]}
    return list(img_data.values())
    
def search_intent(event):
    sentence = event["interpretations"][0]["intent"]["slots"]["Tag"]["value"]["interpretedValue"].lower()
    keywords = {}

    ans = ""
    
    for word in sentence.split(' '):
        keywords[word]=1
    
    ans = ', '.join(list(keywords.keys()))

    # es_search = get_data_es(keywords)
    # print("elastic search: ", es_search)
    response = {
        "results":get_data_es(keywords)
    }

    return response


def lambda_handler(event, context):
    print("event",event)
    print("param",event['queryStringParameters']["q"])
    print(context)
    client = boto3.client('lexv2-runtime')
    
    response = client.recognize_text(
    botId=botId,
    botAliasId=botAliasId,
    localeId='en_US',
    sessionId=userId,
    text=event['queryStringParameters']["q"])
    
    print("response",response)
    # search_intent(response)
    return {
    "isBase64Encoded": False,
    "statusCode": 200,
    "headers":    {"Access-Control-Allow-Headers":"*","Access-Control-Allow-Methods":"*","Access-Control-Allow-Origin":"*"},
    "body":  json.dumps(search_intent(response))
    }

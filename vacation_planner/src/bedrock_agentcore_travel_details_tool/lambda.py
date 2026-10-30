import json
import os

import boto3

def lambda_handler(event, context):
    print(f"Received event: {event}")
    city = event['city']
    client = boto3.client('dynamodb')
    response = client.get_item(
        TableName=os.environ['TRAVEL_TABLE_NAME'],
        Key={
            'city': {'S': city}
        }
    )
    print(response)
    item = response.get('Item')
    if item is None:
        return {
            "statusCode": 404,
            "body": json.dumps({"message": f"No travel packages found for city '{city}'. Use the bare city name."})
        }
    return {
        "statusCode": 200,
        "body": json.dumps(item)
    }

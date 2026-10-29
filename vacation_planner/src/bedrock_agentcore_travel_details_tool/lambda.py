import json

import boto3
import boto3

def lambda_handler(event, context):
    print(f"Received event: {event}")
    city = event['city']
    client = boto3.client('dynamodb')
    response = client.get_item(
        TableName='TravelDetails',
        Key={
            'City': {'S': city}
        }
    )
    print(response)
    return {
        "statusCode": 200,
        "body": json.dumps(response.get('Item'))
    }

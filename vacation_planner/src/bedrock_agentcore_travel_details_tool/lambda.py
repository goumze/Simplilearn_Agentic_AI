import json


def lambda_handler(event, context):
    print(f"Received event: {event}")

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Hello from bedrock_agentcore_travel_details_tool"}),
    }

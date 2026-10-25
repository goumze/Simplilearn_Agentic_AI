import json
import os
import boto3
import os
import uuid

def lambda_handler(event, context):
    #Create a client connection with Bedrock AgentCore

    client = boto3.client('bedrock-agentcore',region_name=os.environ['AGENT_REGION'])
    user_input = event.get('prompt','Mumbai')
    payload = json.dumps({"topic":user_input})

    #Generate sesson id
    session_id = f"lambda_session_{str(uuid.uuid4()).replace('-', '')}"

    print(f"Invoking AgentCore with payload {payload} and session id: {session_id}")

    response = client.invoke_agent_runtime(agentRuntimeArn=os.environ['AGENT_RUNTIME_ARN'],
                                           runtimeSessionId=session_id,
                                           payload=payload,
                                           qualifier="DEFAULT")

    response_body = response['response'].read()

    print(f"AgentCore response: {response_body}")

    response_data = json.loads(response_body)

    return {
        'statusCode': 200,
        'headers':{
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'result': response_data,
            'session_id': session_id
            })
    } 
import os
from pyexpat import model
import warnings
import logging
import time
import litellm
from litellm import completion, completion_cost, Router
from litellm.caching import cache
from dotenv import load_dotenv
from opentelemetry.metrics import Counter
from transformers import Cache
from langchain_litellm import ChatLiteLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import ChatOutputParser, StrOutputParser

load_dotenv()
warnings.filterwarnings("ignore")
logging.getLogger("LiteLLM").setLevel(logging.ERROR)

litellm.suppress_debug_info = True

#Same code, different providers - just change the model string
#Call OpenAI

response_openai = completion(model="gpt-4o-mini",messages=[{"role": "user", "content": "Explain RAG in one sentence"}])

print("Open AI response: ",response_openai.choices[0].message.content)

#Automatic fallback to another model if the primary model fails

response = completion(model="gpt-5x-turbo",
                      messages=[{"role": "user", "content": "Explain RAG in one sentence"}],
                      fallbacks=["gpt-4o-mini","gpt-4o"])

print("Response: ",response.choices[0].message.content[:200],"...")
print("Which model actually answered: ", response.model)
print("\nInput Tokens: ", response.usage.prompt_tokens)
print("Output Tokens: ", response.usage.completion_tokens)
print("Total Tokens: ", response.usage.total_tokens)
completion_cost_data = completion_cost(response)

print(f"Completion cost data: {completion_cost_data:.8f}")

litellm.callback=[]
litellm.success_callback = []
litellm.failure_callback = []
litellm._async_success_callback = []
litellm._async_failure_callback = []

#Also clear any router-strategy state
litellm.cache = None

print("Lite LLM state reset - ready for clean caching demo")

#Enable in-memory caching (you can also use Redis in production)
litellm.cache = Cache(type="local")

prompt = "What does LLM stand for ? Answer in one line."

#First call - actually hits OpenAI

start = time.time()
response1 = completion(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], caching = True)
end = time.time()
print("First call response: ", response1.choices[0].message.content[:200], "...")
print("Time taken for first call: ", end - start, "seconds")

#Second call - should hit the cache
start = time.time()
response2 = completion(model="gpt-4o-mini", messages=[{"role": "user", "content": prompt}], caching = True)
end = time.time()
print("Second call response: ", response2.choices[0].message.content[:200], "...")
print("Time taken for second call: ", end - start, "seconds")

#Smart Routing
model_list = [{
    "model_name":"fast_cheap",
    "litellm_params":{
        "model":"gpt-4o-mini",
        "api_key":os.getenv("OPENAI_API_KEY")
        }
    },
    {
        "model_name":"smart_coding",
        "litellm_params":{
            "model":"gpt-5x-turbo",
            "api_key":os.getenv("OPENAI_API_KEY")
        }
    },
    {
        "model_name":"balanced",
        "litellm_params":{
            "model":"gpt-4o",
            "api_key":os.getenv("OPENAI_API_KEY")
        }
    }
]

router = Router(model_list=model_list)

prompt = "Summarize: AI is changing software development"
fast_response = router.completion(model="fast_cheap", messages=[{"role": "user", "content": prompt}])
print("Fast response: ", fast_response.choices[0].message.content[:200], "...")

smart_response = router.completion(model="smart_coding", messages=[{"role": "user", "content": prompt}])
print("Smart response: ", smart_response.choices[0].message.content[:200], "...")

balanced_response = router.completion(model="balanced", messages=[{"role": "user", "content": prompt}])
print("Balanced response: ", balanced_response.choices[0].message.content[:200], "...")

#Load Balancing Across Multiple API keys

model_list = [{
    "model_name":"gpt-pool",
    "litellm_params": {
        "model":"gpt-4o-mini",
        "api_key":os.getenv("OPENAI_API_KEY")
    },
    "model_info": {"id": "openai-gpt4o"}
    },{
    "model_name":"gpt-pool-2",
    "litellm_params": {
        "model":"gpt-5x-turbo",
        "api_key":os.getenv("OPENAI_API_KEY")
    },
    "model_info": {"id": "openai-gpt5x"}
}]

router = Router(model_list=model_list,routing_strategy="simple-shuffle")

print(f"{'Request':<10}{'Deployment Picked':<22}{'Latency':<12}{'Response':<400}")
print("-"*84)

for i in range(6):
    r = router.completion(model="gpt-pool", messages = [{"role": "user", "content": f"Say hello, request {i+1}"}])

    #Pull out which deployment served this request
    deployment_id = r._hidden_params.get("model_id","unknown")
    latency = r._response_ms
    answer = r.choices[0].message.content[:35]
    print(f"#{i+1:<9}{deployment_id:<22}{latency:>6.0f} ms {answer}")

#Strategy 1: Least Busy

model_list = [
    {
        "model_name":"chat",
        "litellm_params":{
            "model":"gpt-4o-mini",
            "api_key":os.getenv("OPENAI_API_KEY")
        },
        "model_info":{"id":"OpenAI-4"},
    },
    {
        "model_name":"chat",
                "litellm_params":{
                    "model":"gpt-4o-mini",
                    "api_key":os.getenv("OPENAI_API_KEY")
                },
                "model_info":{"id":"OpenAI-5"},
    }]    

router = Router(model_list=model_list,routing_strategy="least-busy")

hits = Counter()
for i in range(8):
    r = router.completion(model="chat",messages=[{"role": "user", "content": f"Say 'OK' #{i}"}], max_tokens=5)

    hits[r._hidden_params.get("model_id","?")] += 1
    print(f"Request {i+1} -> {r._hidden_params.get('model_id','?')}")

    hits[r._hidden_params.get("model_id","?")] += 1
    print(f"Request {i+1} -> {r._hidden_params.get('model_id','?')}")
    print(f" {k}: {'*'*v} ({v})")

#Latency based routing strategy
model_list = [
    {
        "model_name":"chat",
        "litellm_params":{
            "model":"gpt-4o",
            "api_key":os.getenv("OPENAI_API_KEY")
        },
        "model_info":{"id":"OpenAI-4"},
    },
    {
        "model_name":"chat",
        "litellm_params":{
            "model":"gpt-5x-turbo",
            "api_key":os.getenv("OPENAI_API_KEY")
        },
        "model_info":{"id":"OpenAI-5"},
    }]    

router = Router(model_list=model_list,routing_strategy="latency-based-routing")

print("Send 10 requests and watch which deployment get picked over time")
print(f"{'Req':<6}{'Deployment Picked':<32}{'Latency':<10}")
hits = Counter()
for i in range(10):
    r = router.completion(model="chat",messages=[{"role": "user", "content": "Reply with exactly: OK"}], max_tokens=5)
    latency_ms = (time.time() - r._start_time) * 1000
    deployment = r._hidden_params.get("model_id","?")
    print(f"#{i+1:<5}{deployment:<32}{latency_ms:<6.0f} ms")

    deployment = r._hidden_params.get("model_id","?")
    print(f"#{i+1:<5}{deployment:<32}{latency_ms:<6.0f} ms")

#A Standard LangChain prompt template

llm = ChatLiteLLM(model="gpt-4o")

prompt = ChatPromptTemplate.from_messages([
    ("system","You are a helpful AI tutor named Goutam GPT. Be concise"),
    ("user","{question}")
])

#Compose with LCEL
chain = prompt | llm | StrOutputParser()

result = chain.invoke({"question":"What is an LLM Gateway in 3 bullets ?"})
print(result)

#Primary Model
primary_model = ChatLiteLLM(model="gpt-4o")

#Fallbacks (any LangChain-compatible model)
fallback_1 = ChatLiteLLM(model="gpt-4o-mini")
fallback_2 = ChatLiteLLM(model="gpt-5x-turbo")

#LangChain's with_fallbacks() chains them together
robust_llm = primary_model.with_fallbacks(fallback_1, fallback_2)

prompt = ChatPromptTemplate.from_messages([
    ("system","You are an expert AI Engineer. Always reply in JSON: {{\n\"answer\": ...}}"),
    ("user","{question}")
])

chain = prompt | robust_llm | StrOutputParser()

result = chain.invoke({"question":"What are the top 3 benefits of an LLM Gateway ?"})
print(result)




import time
from litellm import completion, completion_cost

def classify_task(user_query: str):
    """Cheap classifier - uses the fastest model to decide routing."""
    cls = completion(model="gpt-4o-mini", 
                     messages=[{
                                "role": "user", 
                                "content": (
                                    f"Classify the following query into EXACTLY one word: "
                                    f"'code','summary', or 'general'. Query: {user_query}\n\nAnswer"
                                    )
                                }],
                    max_tokens=5
                    )
    return cls.choices[0].message.content.strip()

def call_with_fallbacks(model_chain,messages):
    """Try each model in order: return the first one that succeeds."""
    for model in model_chain:
        try:
            return completion(model=model, messages=messages)
        except Exception as e:
            print(f"{model} failed ({type(e).__name__}), trying next model...")
            last_error = e
            continue
    raise last_error

def smart_chat(user_query: str):
    """Routes to the right model based on task type, with fallbacks."""
    task = classify_task(user_query)

    #Each entry is a FULL chain:[primary,fallback1,fallback2,...]
    #Every model name includes its provider prefix 
    routing = {
        "code":["gpt-4o","gpt-5x-mini"],
        "summary":["gpt-4o-mini"],
        "general":["gpt-4o-mini"]
    }

    model_chain = routing.get(task,routing["general"])

    start = time.time()
    response = call_with_fallbacks(model_chain=model_chain,messages=[{"role": "user", "content": user_query}])
    latency= time.time() - start

    try:
        cost = completion_cost(response)
        cost_str = f"${cost:.6f}"
    except Exception as e:
        print(f"Failed to calculate cost ({type(e).__name__}): {e}")
        cost_str = "n/a"

    return {
        "detected_task":task,
        "model_used":response.model,
        "answer":response.choices[0].message.content,
        "latency_sec":round(latency,2),
        "cost": cost_str
    }

#Try it on three very different queries
queries = [
    "Write a Python function to compute Fibonacci numbers",
    "Summarize the importance of attention mechanism in 2 sentences",
    "Tell me a fun fact about elephants"
]

for q in queries:
    print("=" * 70)
    print(" Q: ",q)
    result = smart_chat(q)
    print(f"Task: {result['detected_task']}")
    print(f"Model Used: {result['model_used']}")
    print(f"Answer: {result['answer']}")
    print(f"Latency (sec): {result['latency_sec']}")
    print(f"Cost: {result['cost']}")
import asyncio
import time
import httpx

CHATBOT_URL = "http://localhost:8000/hospital-rag-agent"

async def make_async_post(url, data):
    timeout = httpx.Timeout(timeout=120)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, timeout=timeout)
            response.raise_for_status()  # Raise an error for bad status codes (e.g., 4xx or 5xx)
            
            if response.headers.get("Content-Type") == "application/json":
                return response.json()
            else:
                print(f"Unexpected content type: {response.headers.get('Content-Type')}")
                return response.text
        except httpx.HTTPStatusError as e:
            print(f"HTTP error occurred: {e}")
        except json.JSONDecodeError:
            print("Failed to decode JSON")
            print(f"Response text: {response.text}")
        except Exception as e:
            print(f"An error occurred: {e}")

    return None

async def make_bulk_requests(url, data):
    tasks = [make_async_post(url, payload) for payload in data]
    responses = await asyncio.gather(*tasks)
    
    outputs = [r["output"] for r in responses if r is not None and "output" in r]
    
    return outputs


questions = [
   "What is the current wait time at Wallace-Hamilton hospital?",
   "Which hospital has the shortest wait time?",
   "At which hospitals are patients complaining about billing and insurance issues?",
   "What is the average duration in days for emergency visits?",
   "What are patients saying about the nursing staff at Castaneda-Hardy?",
   "What was the total billing amount charged to each payer for 2023?",
   "What is the average billing amount for Medicaid visits?",
   "How many patients has Dr. Ryan Brown treated?",
   "Which physician has the lowest average visit duration in days?",
   "How many visits are open and what is their average duration in days?",
   "Have any patients complained about noise?",
   "How much was billed for patient 789's stay?",
   "Which physician has billed the most to cigna?",
   "Which state had the largest percent increase in Medicaid visits from 2022 to 2023?",
]

request_bodies = [{"text": q} for q in questions]

start_time = time.perf_counter()
outputs = asyncio.run(make_bulk_requests(CHATBOT_URL, request_bodies))
end_time = time.perf_counter()

print(f"Run time: {end_time - start_time} seconds")
#Run time: 37.90156063800032 seconds
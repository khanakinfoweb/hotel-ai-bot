from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
import requests

app = FastAPI()

# Enable CORS so any of your hotel websites can talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load Groq API Key from environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Load multi-hotel database
with open("hotels_db.json", "r") as f:
    HOTELS_DATA = json.load(f)

class ChatRequest(BaseModel):
    hotel_id: str
    message: str

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    # 1. Fetch specific hotel content dynamically
    hotel_info = HOTELS_DATA.get(req.hotel_id)
    if not hotel_info:
        raise HTTPException(status_code=404, detail="Hotel ID not found in database.")

    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY environment variable missing.")

    # 2. Build the tailored system prompt for THIS specific hotel
    system_prompt = f"""
    You are the official AI Receptionist for {hotel_info['name']}.
    Use ONLY the following details to answer guest queries accurately:

    [HOTEL DETAILS]
    {hotel_info['details']}

    [ROOM RATES]
    {hotel_info['pricing']}

    [POLICIES & RULES]
    {hotel_info['rules']}

    [BOOKING & LEAD INSTRUCTIONS]
    If the guest wants to make a booking, politely ask for their:
    1. Full Name
    2. Check-in & Check-out Dates
    3. Phone Number or Email
    Then reply: "Thank you! Our front desk team at {hotel_info['name']} has noted your request and will contact you directly to confirm your booking."
    Do NOT offer price discounts or invent rules outside of this provided context.
    """

    # 3. Request completion from Groq API (Free Tier)
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": req.message}
        ],
        "temperature": 0.2
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        bot_reply = response.json()['choices'][0]['message']['content']
        return {"reply": bot_reply}
        
    return {"reply": "Sorry, our reception system is temporarily busy. Please contact the front desk directly."}
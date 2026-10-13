from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
from bs4 import BeautifulSoup

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HOTEL_URL = "https://librishhotel.com/"

# Global variable to store scraped content in memory so it replies instantly!
CACHED_HOTEL_CONTENT = ""

def load_hotel_content():
    global CACHED_HOTEL_CONTENT
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(HOTEL_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            for script in soup(["script", "style", "nav", "footer"]):
                script.extract()
            text = soup.get_text(separator=' ')
            CACHED_HOTEL_CONTENT = " ".join(text.split())[:10000]
            print("Successfully scraped and cached hotel website content!")
    except Exception as e:
        print(f"Error scraping on startup: {e}")

# Scrape the website automatically the moment the server starts
@app.on_event("startup")
def startup_event():
    load_hotel_content()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY missing.")

    global CACHED_HOTEL_CONTENT
    if not CACHED_HOTEL_CONTENT:
        load_hotel_content() # Fallback reload if empty

    # Build system instructions using the cached website memory
    system_prompt = f"""
    You are the official AI Receptionist for Hotel The Librish (librishhotel.com).
    Use ONLY the following live website text content to answer guest questions accurately:

    [HOTEL WEBSITE DATA]
    {CACHED_HOTEL_CONTENT}

    [BOOKING & LEAD INSTRUCTIONS]
    If the guest wants to make a booking or reserve a room, politely ask for their:
    1. Full Name
    2. Check-in & Check-out Dates
    3. Phone Number or Email
    Then reply: "Thank you! Our front desk team at Hotel The Librish has noted your request and will contact you directly to confirm your booking."
    Do NOT invent prices or rules not found in the website data.
    """

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": req.message}
        ],
        "temperature": 0.2
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return {"reply": response.json()['choices'][0]['message']['content']}
        
    return {"reply": f"API Error: {response.text}"}

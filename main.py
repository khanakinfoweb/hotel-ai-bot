from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# Allow your hotel website domain to connect safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HOTEL_URL = "https://librishhotel.com/"

# Cache variable to hold live website content in server memory
CACHED_HOTEL_CONTENT = ""

def scrape_hotel_website():
    """Dynamically reads and cleans text directly from https://librishhotel.com/"""
    global CACHED_HOTEL_CONTENT
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(HOTEL_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove scripts, styles, navigation, and footers to keep text relevant
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.extract()
                
            text = soup.get_text(separator=' ')
            CACHED_HOTEL_CONTENT = " ".join(text.split())[:12000]
            print("Successfully scraped live content from librishhotel.com!")
    except Exception as e:
        print(f"Error scraping hotel website: {e}")

# Automatically scrape when the server boots up
@app.on_event("startup")
def startup_event():
    scrape_hotel_website()

class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
def chat_endpoint(req: ChatRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY missing.")

    global CACHED_HOTEL_CONTENT
    if not CACHED_HOTEL_CONTENT:
        scrape_hotel_website()

    # Dynamic system prompt powered by your live website text
    system_prompt = f"""
    You are the official, friendly AI Receptionist for Hotel The Librish (librishhotel.com).
    Use ONLY the following live scraped website content to answer guest questions accurately:

    [LIVE WEBSITE CONTENT FROM LIBRISHHOTEL.COM]
    {CACHED_HOTEL_CONTENT}

    [BOOKING & LEAD INSTRUCTIONS]
    If a guest wants to book a room or inquire about a reservation, politely ask for their:
    1. Full Name
    2. Preferred Room Type
    3. Check-in & Check-out Dates
    4. Phone Number or Email
    Then reply: "Thank you! Our front desk team at Hotel The Librish has noted your booking request and will contact you shortly to confirm."
    Do NOT invent prices or details not found in the live website content. Keep answers polite and concise.
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

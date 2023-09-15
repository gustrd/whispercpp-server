import os
import time
import httpx
import threading
from dotenv import load_dotenv
from datetime import datetime
from fastapi import FastAPI, UploadFile, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from subprocess import Popen

from app.services.speech_to_text_service import SpeechToTextService

load_dotenv()
SECRET_TOKEN = os.getenv('SECRET_TOKEN')
SUBDOMAIN = os.getenv('SUBDOMAIN')
PORT = int(os.getenv('PORT'))

app = FastAPI(port=PORT)

requests_dict = {}

def check_health_and_start_tunnel():
    awaiting = True
    while awaiting:
        try:
            response = httpx.get(f"http://127.0.0.1:{PORT}/")
            if response.status_code == 200:
                awaiting = False
                # LT Tunnel
                Popen(["lt", "--port", str(PORT), "--subdomain", SUBDOMAIN,"--local-host", "127.0.0.1", "-o", "--print-requests"], shell=True)
        except Exception as e:
            print(e)
            time.sleep(5)  
            awaiting = True

async def download_file(url, filename) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()

        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)

        file_name = f"{current_time}_{filename}"
        file_path = os.path.join(temp_dir, file_name)  
        with open(file_path, 'wb') as file:
            file.write(response.content)
        
    return file_path

@app.on_event("startup")
async def startup_event():
    threading.Thread(target=check_health_and_start_tunnel).start()

def get_current_user(token: str = Header(...)):
    if token != SECRET_TOKEN:
        raise HTTPException(
            status_code=400,
            detail="Invalid token"
        )
    return token

@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.post("/transcribe_file_now")
async def transcribe_file(file: UploadFile, user: str = Depends(get_current_user)):
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    file_name = f"{current_time}_{file.filename}"
    file_path = os.path.join(temp_dir, file_name)  
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    
    transcription = SpeechToTextService.audio_path_to_text(file_path)

    try:
        os.remove(file_path)
    finally:
        return transcription

@app.post("/request_transcribe_file_url")
async def request_transcribe_file(url: str, user: str = Depends(get_current_user)):
    global requests_dict
    file_path = await download_file(url, 'audio')
    
    thread = threading.Thread(target=SpeechToTextService.audio_path_to_text, args=(file_path, requests_dict))
    thread.start()

    key = file_path.replace('\\','')
    return key

@app.get("/check_transcribe_file")
async def check_transcribe_file(key: str, user: str = Depends(get_current_user)):
    key = key.replace('\\','')

    if key in requests_dict.keys():
        if requests_dict[key]:
            transcription = requests_dict[key]
            del requests_dict[key]
            return JSONResponse(content=transcription, status_code=200)  # HTTP 200 OK
        else:
            return JSONResponse(content={'detail': 'PENDING'}, status_code=202)  # HTTP 202 Accepted / # HTTP 504 Timeout
    else:
        return JSONResponse(content={'detail': 'NOT FOUND'}, status_code=404)  # HTTP 404 Not Found 

    

    
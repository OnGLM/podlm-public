import logging
import requests
import json
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import httpx
import os
import tempfile
from pydub import AudioSegment
from urllib.parse import urlencode
from urllib.parse import quote_plus

# Set up the logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

API_KEY = "你的API_Key"            
SECRET_KEY = "你的Secret_Key" 
# 发音人选择, 基础音库：0为度小美，1为度小宇，3为度逍遥，4为度丫丫，
# 精品音库：5为度小娇，103为度米朵，106为度博文，110为度小童，111为度小萌，默认为度小美 
PER = 0
PER_Guest = 1
# 语速，取值0-15，默认为5中语速
SPD = 5
# 音调，取值0-15，默认为5中语调
PIT = 5
# 音量，取值0-9，默认为5中音量
VOL = 5
# 下载的文件格式, 3：mp3(default) 4： pcm-16k 5： pcm-8k 6. wav
AUE = 6

CUID = "123456PYTHON"

app = FastAPI()
def get_access_token():
    """
    使用 AK，SK 生成鉴权签名（Access Token）
    :return: access_token，或是None(如果错误)
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {"grant_type": "client_credentials", "client_id": API_KEY, "client_secret": SECRET_KEY}
    return str(requests.post(url, params=params).json().get("access_token"))

# API URL and Key
API_URL = 'http://tsn.baidu.com/text2audio'      

@app.get("/tts")
async def text_to_speech(text: str, background_tasks: BackgroundTasks,voice: str):

    temp_wav_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False) 
    logger.info(f"Created temp WAV file: {temp_wav_file.name}")

    if voice == "host":
         params = {'tok': get_access_token(), 'tex': quote_plus(text), 'per': PER, 'spd': SPD, 'pit': PIT, 'vol': VOL, 'aue': AUE, 'cuid': CUID,
              'lan': 'zh', 'ctp': 1}  # lan ctp 固定参数
    else:
         params = {'tok': get_access_token(), 'tex': quote_plus(text), 'per': PER_Guest, 'spd': SPD, 'pit': PIT, 'vol': VOL, 'aue': AUE, 'cuid': CUID,
              'lan': 'zh', 'ctp': 1}  # lan ctp 固定参数

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'audio/wav'
    }
    data = urlencode(params)
    
    async with httpx.AsyncClient() as client:
        try:
            logger.info("Sending request ...")
            response = await client.post(API_URL, headers=headers, data=data.encode('utf-8'))
            response.raise_for_status()  # Raise for HTTP errors

             # Log the content type of the response
            content_type = response.headers.get('Content-Type', 'unknown')
            logger.info(f"Response Content-Type: {content_type}")

            # Save the response content as an WAV file
            with open(temp_wav_file.name, "wb") as audio_file:
                audio_file.write(response.content)
            logger.info(f"Audio written to temp WAV file: {temp_wav_file.name}")

            # Use FileResponse to send the WAV file
            file_response = FileResponse(temp_wav_file.name, media_type="audio/wav", filename="speech.wav")
            logger.info("Returning the WAV audio file.")

            # Add a background task to delete the files after response is sent
            background_tasks.add_task(os.remove, temp_wav_file.name)
            return file_response

        except httpx.TimeoutException:
            logger.error("Request timed out. Consider increasing the timeout limit.")
            raise HTTPException(status_code=504, detail="Gateway Timeout: OpenAI API did not respond in time.")
        except Exception as e:
            logger.error(f"Error occurred: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5012)

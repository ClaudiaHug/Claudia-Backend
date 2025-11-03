# app.py
# app.py
from flask import Flask, jsonify
from flask_cors import CORS
import requests
import time 
import os 
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta


app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:5173", "https://app-claudia-test2-brbmcmbvaebvadhc.spaincentral-01.azurewebsites.net"]}})



# ⚠️ Hardcoded credentials (solo para pruebas)
CONNECT_STR = "DefaultEndpointsProtocol=https;AccountName=stclaudiastoragevideo;AccountKey=KCQkkWCTJFxWTTl3a1aX/V6bKc5BwmcblsA2szvzbh0JvtzY6QJyLadeftultrQPX9euOUbbRxif+AStvRD/pw==;EndpointSuffix=core.windows.net"
ACCOUNT_NAME = "stclaudiastoragevideo"
ACCOUNT_KEY = "KCQkkWCTJFxWTTl3a1aX/V6bKc5BwmcblsA2szvzbh0JvtzY6QJyLadeftultrQPX9euOUbbRxif+AStvRD/pw=="
CONTAINER_NAME = "videos"

#AZURE Storage Configuration para hacerlo con variables de entorno

#CONNECT_STR = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
#CONTAINER_NAME = "videos"
#ACCOUNT_NAME = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
#ACCOUNT_KEY = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')


#SORA API config

ENDPOINT = "https://oai-techinnovationsandboxbuild-eu2.cognitiveservices.azure.com"
API_KEY = "Aks9EGFuINr384iaQaldoh0YBMRZ5gX4YNR8r8zuDMMNDiPY8qyJJQQJ99BDACHYHv6XJ3w3AAABACOGIfMz" # Guarda tu API key en variable de entorno
API_VERSION = "preview"
HEADERS = {"api-key": API_KEY, "Content-Type": "application/json"}

@app.get("/api/hello")
def hello():
    return jsonify(message="Hello, world!")
    #return{
        
        #"Hello, World"
       # }
        
    


@app.post("/api/generate-video")
def generate_video():
    data = request.get_json()
    prompt = data.get("prompt")
    
# 1. Crear job en Sora
    create_url = f"{ENDPOINT}/openai/v1/video/generations/jobs?api-version={API_VERSION}"
    body = {
        "prompt": prompt,
        "width": 1280,
        "height": 720,
        "n_seconds": 20,
        "model": "video-gen-v1"
    }
    
    response = requests.post(create_url, headers=HEADERS, json=body)
    response.raise_for_status()
    job_id = response.json()["id"]

# 2. Poll for job status
    status_url = f"{ENDPOINT}/openai/v1/video/generations/jobs/{job_id}?api-version={API_VERSION}"
    status=None
    while status not in ("succeeded", "failed", "cancelled"):
        time.sleep(5)  # Wait before polling again
        status_response = requests.get(status_url, headers=HEADERS).json()
        status = status_response.get("status")
        print(f"Job status: {status}")

    # 3. Retrieve generated video 
    if status == "succeeded":
        generations = status_response.get("generations", [])
        if generations:
            print(f"✅ Video generation succeeded.")
            generation_id = generations[0].get("id")
            video_url = f"{ENDPOINT}/openai/v1/video/generations/{generation_id}/content/video?api-version={API_VERSION}"
            video_response = requests.get(video_url, headers=HEADERS)
            if video_response.ok:
                output_path = "output.mp4"
                with open(output_path, "wb") as file:
                    file.write(video_response.content)
                    print(f'Generated video saved as "{output_path}"')
        else:
            raise Exception("No generations found in job result.")
    else:
        raise Exception(f"Job didn't succeed. Status: {status}")
    
    #SUBIR VIDEOA BLOB STORAGE 
    
    blob_name = f"video_{int(datetime.utcnow().timestamp())}.mp4"
    blob_service_client = BlobServiceClient.from_connection_string(CONNECT_STR)
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=blob_name)
    with open(output_path, "rb") as video_file:
        blob_client.upload_blob(video_file, overwrite=True)

    
# 5. Generar SAS token
    sas_token = generate_blob_sas(
        account_name=ACCOUNT_NAME,
        container_name=CONTAINER_NAME,
        blob_name=blob_name,
        account_key=ACCOUNT_KEY,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.utcnow() + timedelta(hours=1)
    )
    
    final_url = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{CONTAINER_NAME}/{blob_name}?{sas_token}"

    return jsonify({"videoUrl": final_url})



if __name__ == "__main__":
    # Ejecutar en desarrollo
    app.run(host="127.0.0.1", port=5000, debug=True)

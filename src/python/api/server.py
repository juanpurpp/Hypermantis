from fastapi import FastAPI, File, UploadFile, WebSocket
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.responses import StreamingResponse
import spectral as spy
import numpy as np
import uuid
import orjson 
import json
from processing.decode import decode
import os
app = FastAPI()
import tempfile

# Obtener la ruta de la carpeta temporal
temp_dir = os.path.join(tempfile.gettempdir(), 'hypermantis')
print(f"La carpeta temporal del sistema es: {temp_dir}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Permitir todos los headers
)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=5)
@app.get('/')
async def status():
    return JSONResponse({'message': 'Server is running'})


@app.post("/process")
async def process_image(files: list[UploadFile] = File(...)):
    print('Start file processing')
    if len(files) != 2:
        return JSONResponse({'message': 'Two files are required: data and header'}, status_code=400)

    os.makedirs(temp_dir, exist_ok=True)
    transaction_name = str(uuid.uuid4())
    data_file_location = os.path.join(temp_dir, transaction_name+'.bip')  
    header_file_location = os.path.join(temp_dir, transaction_name+'.bip.hdr')  

    with open(data_file_location, "wb") as data_f:
        data_f.write(files[0].file.read())
    with open(header_file_location, "wb") as header_f:
        header_f.write(files[1].file.read())

    result = {
        'message': 'Image processed successfully',
        'transaction_name': transaction_name,
    }
    return result

@app.get("/as_image")
async def get_as_image(transaction_name: str):
    data_filename = os.path.join(temp_dir, transaction_name+'.bip')
    header_filename = os.path.join(temp_dir, transaction_name+'.bip.hdr')
    image = decode(data_filename, header_filename)

    rgb_image = image.get_rgb_composition()
    image.save_rgb()
    return {'message':'image created', 'data': rgb_image[:,:,:].tolist()}

@app.get("/get_pixel_info")
async def get_pixel_info(transaction_name: str, x: int, y: int):
    data_filename = os.path.join(temp_dir, transaction_name+'.bip')
    header_filename = os.path.join(temp_dir, transaction_name+'.bip.hdr')
    image = decode(data_filename, header_filename)
    pixel = image.img[y,x]
    return {'message': 'pixel info', 'pixel': zip(image.bands, pixel.tolist())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

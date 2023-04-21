import asyncio
import uuid as uuid_pkg
from uuid import UUID
from fastapi import FastAPI, status, File, UploadFile, Response, BackgroundTasks
import cv2
from typing import Any, List
import os
import logging

logging.basicConfig(filename='example.log', encoding='utf-8', level=logging.DEBUG)


app = FastAPI()

iterator = 0
files = {}
gathered_data = {}
processing = False
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades +'haarcascade_frontalface_default.xml')
eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades +'haarcascade_eye.xml')
smile_cascade = cv2.CascadeClassifier(cv2.data.haarcascades +'haarcascade_smile.xml')


@app.get("/")
async def read_root():
    return {"Hello": "i'm here!"}


@app.post("/upload_file/", status_code=status.HTTP_200_OK)
async def receiveVideo(file: UploadFile, response: Response):
    uuid = str(uuid_pkg.uuid4())
    if("image" in file.content_type):
        response.headers["file-uuid"] = uuid
        files[uuid] = file
        asyncio.create_task(start_detection_process_image(uuid))
        return{"Success!": "Image added and uuid attached!"}
    if("video" in file.content_type):
        logging.debug("Received video type file")
        logging.debug(f"File infos; Localization: {file.file.name}, Name: {file.filename}, Size: {file.size}")
        response.headers["file-uuid"] = uuid
        files[uuid] = file
        filename = os.path.join("/tmp", f"{uuid}.{file.filename.split('.')[-1]}")
        with open(filename, "wb") as f:
            f.write(file.file.read())
        asyncio.create_task(start_detection_process_video(uuid))
        return[
            {"Success!": "Video added and uuid attached!"},
            {"File localization:": f"{file.file.name}"},
            {"File name:":f"{file.filename}"}
               ]
    return {"file_size": file.content_type}

@app.get('/healthcheck', status_code=status.HTTP_200_OK)
async def perform_healthcheck():
    return {'healthcheck': 'Everything OK!'}

@app.get("/data_by_uuid/{uuid}")
async def get_data_by_uuid(uuid: UUID, response: Response):
    global processing
    if str(uuid) in gathered_data:
        x_list = gathered_data[str(uuid)].get('x', [])
        y_list = gathered_data[str(uuid)].get('y', [])
        return [{"milisec": x_list[i], "smiles": y_list[i]} for i in range(len(x_list))]
    if(processing):
        response.status_code = status.HTTP_102_PROCESSING
        return {"Data is still being processed":"be patient!"}
        

@app.get("/latest_upload_data")
async def get_latest_data(response: Response):
    global iterator
    global processing
    return_data = []
    for uuid, data in gathered_data.items():
        x_list = data.get('x', [])
        y_list = data.get('y', [])
        if data.get('counter') == iterator:
            for i in range(len(x_list)):
                return_data.append({"milisec": x_list[i], "smiles": y_list[i]})
            return return_data
    if len(gathered_data) == 0 and processing==False:
        return {"No data found": "Sorry!"}
    if(processing):
        response.status_code = status.HTTP_102_PROCESSING
        return {"Data is still being processed":"be patient!"}

async def start_detection_process_video(uuid):
    global iterator
    global processing
    logging.debug("Start video detection function")
    processing = True
    iterator = iterator + 1
    datapoints_x = []
    datapoints_y = []
    video_capture = cv2.VideoCapture(files[uuid].file.name)
    while video_capture.isOpened():
        logging.debug("Started processing")
        frame_exists, frame = video_capture.read() 
        if frame_exists:
            loop = asyncio.get_event_loop()               
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = await loop.run_in_executor(None, face_cascade.detectMultiScale, gray, 1.3, 5)
            amount_of_smiles = 0
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), ((x + w), (y + h)), (255, 0, 0), 2)
                roi_gray = gray[y:y + h, x:x + w]
                roi_color = frame[y:y + h, x:x + w]
                smiles = await loop.run_in_executor(None, smile_cascade.detectMultiScale, roi_gray, 1.8, 20)
                amount_of_smiles += len(smiles)
                for (sx, sy, sw, sh) in smiles:
                    cv2.rectangle(roi_color, (sx, sy), ((sx + sw), (sy + sh)), (0, 0, 255), 2)

            datapoints_x.append(video_capture.get(cv2.CAP_PROP_POS_MSEC))
            datapoints_y.append(amount_of_smiles)
        else:
            logging.debug("Can't open video file")
            break
    gathered_data[uuid] = {
        'counter': iterator,
        'x': datapoints_x,
        'y': datapoints_y
    }
    processing = False
    video_capture.release()

async def start_detection_process_image(uuid):
    global iterator
    global processing
    processing = True
    iterator = iterator + 1
    datapoints_x = []
    datapoints_y = []
    image = cv2.imread(files[uuid].filename)
    if image:
        loop = asyncio.get_event_loop()               
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = await loop.run_in_executor(None, face_cascade.detectMultiScale, gray, 1.3, 5)
        amount_of_smiles = 0
        for (x, y, w, h) in faces:
            cv2.rectangle(image, (x, y), ((x + w), (y + h)), (255, 0, 0), 2)
            roi_gray = gray[y:y + h, x:x + w]
            roi_color = image[y:y + h, x:x + w]
            smiles = await loop.run_in_executor(None, smile_cascade.detectMultiScale, roi_gray, 1.8, 20)
            amount_of_smiles += len(smiles)
            for (sx, sy, sw, sh) in smiles:
                cv2.rectangle(roi_color, (sx, sy), ((sx + sw), (sy + sh)), (0, 0, 255), 2)

        datapoints_x.append(1)
        datapoints_y.append(amount_of_smiles)
        
        gathered_data[uuid] = {
            'counter': iterator,
            'x': datapoints_x,
            'y': datapoints_y
        }
    else:
        gathered_data[uuid] = {
            'failed' : 'sorry'
        }
    processing = False
import os, io, torch
from PIL import Image
from fastapi import FastAPI, Request, File, UploadFile

device = 'cuda' if torch.cuda.is_available() else 'cpu'
model = torch.load('weights.pth')

app = FastAPI()

@app.post("/predict")
def predict(reqest: Request, file:UploadFile=File(...)):
    data = file.file.read()
    image = Image.open(io.BytesIO(data))
    result = model.predict(image)
    return result
print("hello")
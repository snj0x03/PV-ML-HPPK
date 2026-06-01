# PV-ML-HPPK

HP LaserJet printer part identification system using YOLO11 object detection. Upload a photo of a printer part; the system detects it, draws a bounding box, and returns the part name, serial number, and confidence score from a local database.

---

## Table of Contents

- [Overview](#overview)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Setup](#setup)
- [Database Initialization](#database-initialization)
- [Running the Server](#running-the-server)
- [API Reference](#api-reference)
- [Frontend](#frontend)
- [Docker](#docker)
- [Model](#model)
- [Part Classes](#part-classes)

---

## Overview

The system is built around three components:

1. **YOLO11 model** (`models/best.pt`) — trained to detect 40 HP LaserJet printer part classes from images.
2. **FastAPI backend** (`app/main.py`) — receives image uploads, runs inference, annotates the image with bounding boxes, and returns structured JSON including a base64-encoded annotated image.
3. **SQLite database** (`app/printer_parts.db`) — maps YOLO class IDs to real part names and serial numbers.

---

## Project Structure

```
PV-ML-HPPK/
├── app/
│   ├── main.py            # FastAPI application and /predict endpoint
│   ├── database.py        # SQLAlchemy ORM models and DB engine setup
│   ├── utils.py           # YOLO inference helper (process_and_predict)
│   ├── db_uploader.py     # Imports Roboflow YOLO-format dataset into the DB
│   ├── update_part.py     # Updates DB entries with real part names and serial numbers
│   ├── sdd.py             # Standalone YOLO model load and predict demo
│   ├── index.html         # Frontend UI (served at GET /)
│   ├── Dockerfile         # Docker build definition
│   └── .gitignore         # Excludes roboflow_data/, DB file, venv
├── src/
│   ├── train.py           # Training script (stub)
│   ├── eval.py            # Evaluation script (stub)
│   ├── load.py            # Data loading script (stub)
│   ├── tests.py           # Test suite (stub)
│   └── utils.py           # Shared utilities (stub)
├── models/
│   └── best.pt            # Trained YOLOv8 weights (not tracked in git)
├── config.yml             # Configuration file
├── requirements.txt       # Python dependencies
└── readme.md
```

---

## Requirements

- Python 3.10+
- PyTorch 2.12+ (CPU or CUDA)
- See `requirements.txt` for the full pinned dependency list.

Key packages:

| Package | Version | Purpose |
|---|---|---|
| `ultralytics` | 8.4.58 | YOLO11 model inference |
| `fastapi` | 0.136.3 | Web framework |
| `uvicorn` | 0.48.0 | ASGI server |
| `sqlalchemy` | 2.0.50 | ORM / SQLite access |
| `pillow` | 12.2.0 | Image loading and conversion |
| `torch` | 2.12.0 | Deep learning backend |
| `torchvision` | 0.27.0 | Vision utilities |

---

## Setup

**1. Clone the repository**

```bash
git clone <repo-url>
cd PV-ML-HPPK
```

**2. Create and activate a virtual environment**

```bash
python -m venv fastapi-venv
# Windows
fastapi-venv\Scripts\activate
# Linux / macOS
source fastapi-venv/bin/activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

**4. Place the trained model**

Put the trained YOLOv8 weights at:

```
models/best.pt
```

The server will fail to start if this file is missing.

---

## Database Initialization

The database stores the mapping between YOLO class IDs and real HP part names and serial numbers. Run these two scripts once before starting the server for the first time.

**Step 1 — Create the schema and import dataset images**

Place your Roboflow-exported dataset (YOLO v8 format) at:

```
app/roboflow_data/train/
    images/   ← .jpg / .jpeg / .png files
    labels/   ← matching .txt label files
```

Then run:

```bash
cd app
python db_uploader.py
```

This creates `printer_parts.db`, registers all images and bounding boxes, and creates part entries named `YOLO_Class_0` through `YOLO_Class_39`.

**Step 2 — Update part entries with real names and serial numbers**

```bash
python update_part.py
```

This replaces the `YOLO_Class_N` placeholder names with the actual HP part names and serial numbers (e.g., class 0 becomes `SVC_HP LaserJet Fuser 220V Kit`, serial `5PN77-67001`).

Both scripts are idempotent — re-running them is safe.

---

## Running the Server

From the `app/` directory:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at `http://localhost:8000`.

---

## API Reference

### `GET /`

Returns the frontend HTML page (`index.html`).

---

### `POST /predict`

Run inference on an uploaded image.

**Request**

- Content-Type: `multipart/form-data`
- Field: `file` — the image file (JPEG, PNG, etc.)

**Response**

```json
{
  "part_name": "SVC_HP LaserJet Fuser 220V Kit",
  "serial_number": "5PN77-67001",
  "model_number": "string",
  "confidence": 0.9452,
  "message": "AI 부품 식별 및 바운딩 박스 시각화 완료!",
  "image_base64": "<base64-encoded JPEG string>"
}
```

| Field | Type | Description |
|---|---|---|
| `part_name` | string | Detected HP part name, or `"Unknown"` if nothing detected |
| `serial_number` | string | Part serial number from DB, or `"N/A"` |
| `model_number` | string | Model number from DB, or `"N/A"` |
| `confidence` | float | YOLOv8 detection confidence (0.0–1.0) |
| `message` | string | Status message describing the result |
| `image_base64` | string | Base64-encoded JPEG of the image with bounding boxes drawn; original image returned if nothing was detected |

**Example (curl)**

```bash
curl -X POST http://localhost:8000/predict \
  -F "file=@part_photo.jpg"
```

---

## Frontend

The web UI is served at `GET /` and is a single HTML file (`app/index.html`) with no external dependencies.

Features:
- Drag-and-drop or click-to-upload image selection
- Image preview in the upload zone
- On detection, the preview is replaced with the YOLO11 annotated image (bounding boxes drawn)
- Results panel showing part name, serial number, and confidence percentage

---

## Docker

Build and run the application in a container:

```bash
cd app
docker build -t pv-ml-hppk .
docker run -p 8000:8000 pv-ml-hppk uvicorn main:app --host 0.0.0.0 --port 8000
```

The Dockerfile is based on `ultralytics/ultralytics:latest` which includes PyTorch and CUDA support.

Note: mount or copy `models/best.pt` into the container before running inference.

---

## Model

The model file `models/best.pt` is a YOLO11 checkpoint trained on a Roboflow-annotated dataset of HP LaserJet printer parts. It is not tracked in this repository.

At server startup, the model is loaded once into memory and reused for all subsequent requests.

Inference is run with `conf=0.01` (low confidence threshold) to maximize detection recall. The highest-confidence detection in each image is used for the final result.

---

## Part Classes

The YOLO11 model detects 40 HP LaserJet part classes (IDs 0–39). Full mapping defined in `app/update_part.py`.

| Class ID | Part Name | Serial Number |
|---|---|---|
| 0 | SVC_HP LaserJet Fuser 220V Kit | 5PN77-67001 |
| 1 | SVC_HP LaserJet CYM Managed Imaging Drum | W9078-67001 |
| 2 | SVC_HP LaserJet Black Managed Imaging Drum | W9077-67001 |
| 3 | SVC_HP LaserJet Toner Collection Unit | 6SB85-67001 |
| 4 | Waste toner duct unit | JC96-13015A |
| 5 | SVC_HP LaserJet Trays 2-x Roller Kit | 5PN66-67001 |
| 6 | SVC_HP LaserJet Yellow Developer Unit | 5PN73-67003 |
| 7 | Hard disk 500GB SED | 933853-011 |
| 8 | HP LaserJet ADF Maintenance Kit | 5RC00-67001 |
| 9 | Main PCA (Formatter) | 6CF14-67011 |
| 10 | Laser scanner unit (LSU) | JC97-05149A |
| 11 | Control panel (10.1 inch) | 5QK42-60104 |
| 12 | SVC_T2 transfer assembly | 5PN80-67002 |
| 13 | Low Voltage Power Supply (LVPS), 220V | JC44-00150C |
| 14 | High Voltage Power Supply (HVPS) | JC44-00240C |
| 15 | SVC_HPLJ 300ipm300shtFlw DADFhighspdScnr | 5QK39-67002 |
| 16 | ADF Whole Unit Kit, Valiant A3 | 5QK08-67014 |
| 17 | Fuser drive board (FDB), 220V | JC44-00236C |
| 18 | SVC-Flat Cable, Faro SICB 50pin | 5QK08-67011 |
| 19 | SVC-Flat Cable, Faro SICB 68pin | 5QK08-67012 |
| 20 | FLAT CABLE-LSU | 5QK03-50003 |
| 21 | Exit unit | JC90-01856A |
| 22 | Right door assembly | JC95-02247A |
| 23 | Front cover assembly | 6ER04-61001 |
| 24 | Registration unit assembly | 8GS05-60128 |
| 25 | Registration sensor | 0604-001381 |
| 26 | Feed 2 sensor | 0604-001490 |
| 27 | Fuser, Exit drive assembly | JC93-01850A |
| 28 | Drum, ITB motor | JC31-00123C |
| 29 | Reservoir drive motor | JC93-01659A |
| 30 | Tray 3 empty sensor | 3SJ00-60110 |
| 31 | Duplex 1 motor | JC93-00336A |
| 32 | Toner dispense motor | SS216-80501 |
| 33 | CPR shutter motor | JC31-00078A |
| 34 | LVPS fan | JC31-00198A |
| 35 | FDB fan | JC31-00154A |
| 36 | LSU fan assembly | JC93-01019A |
| 37 | Right door switch assembly | JC93-01467A |
| 38 | Front door switch assembly | JC93-00466A |
| 39 | Outer environment sensor assembly | 5QJ90-40002 |

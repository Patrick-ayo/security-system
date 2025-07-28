#!/usr/bin/env python3
"""
Object Detection Module
Uses YOLOv8 or MMDetection for detecting suspicious objects like phones, weapons, bottles
"""

import cv2
import numpy as np
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import threading

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("YOLOv8 not available")

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("PyTorch not available")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import base64
import numpy as np
import cv2
from ultralytics import YOLO
import io
from PIL import Image
import uvicorn

app = FastAPI()

# Allow CORS for local Electron app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load YOLOv8 model (coco)
model = YOLO("yolov8n.pt")  # Use yolov8n for speed, yolov8s/yolov8m for more accuracy

# Define harmful objects (expand as needed)
HARMFUL_OBJECTS = [
    'gun', 'knife', 'weapon', 'bottle', 'alcohol', 'cigarette', 'lighter', 'pills', 'drug', 'explosive', 'scissors', 'firearm', 'syringe'
]

class DetectionRequest(BaseModel):
    image_base64: str

class DetectionBox(BaseModel):
    label: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]
    harmful: bool
    reason: str

class DetectionResponse(BaseModel):
    detections: List[DetectionBox]

@app.post("/detect", response_model=DetectionResponse)
async def detect_objects(req: DetectionRequest):
    # Decode base64 image
    image_data = base64.b64decode(req.image_base64)
    image = Image.open(io.BytesIO(image_data)).convert("RGB")
    frame = np.array(image)
    
    # Run YOLOv8 detection
    results = model(frame)
    detections = []
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            label = model.names[int(box.cls[0])]
            # Judge harmfulness
            is_harmful = any(h in label.lower() for h in HARMFUL_OBJECTS)
            reason = "Harmful object detected" if is_harmful else "Safe object"
            detections.append(DetectionBox(
                label=label,
                confidence=conf,
                bbox=[x1, y1, x2, y2],
                harmful=is_harmful,
                reason=reason
            ))
    return DetectionResponse(detections=detections)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 
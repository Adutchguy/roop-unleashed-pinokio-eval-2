import os
import sys
import torch
import cv2
import numpy as np
from PIL import Image
from typing import Any, Dict

# 1. Force Python to see the local GroundingDINO folder FIRST
dino_path = os.path.abspath("GroundingDINO")
if dino_path not in sys.path:
    sys.path.insert(0, dino_path)

# 2. Now import from the local folder
try:
    from groundingdino.util.inference import load_model as load_groundingdino, predict
    print("Grounding DINO logic loaded.")
except ImportError as e:
    print(f"Critical Error: Could not load DINO logic. Path: {dino_path}. Error: {e}")

from segment_anything import sam_model_registry, SamPredictor
from clipseg.clipseg import CLIPDensePredT
from roop.utilities import get_device
import roop.globals

class Mask_GroundedSAM:
    processorname = 'mask_groundedsam'
    type = 'mask'

    def __init__(self):
        self.groundingdino_model = None
        self.sam_predictor = None
        self.clipseg_model = None
        self.device = None

    def Initialize(self, options: Dict[str, Any]):
        self.device = get_device()
        torch.set_grad_enabled(False)

        # Load Grounding DINO
        try:
            config_path = "GroundingDINO/groundingdino/config/GroundingDINO_SwinT_OGC.py"
            checkpoint_path = "models/GroundingDINO/groundingdino_swint_ogc.pth"
            self.groundingdino_model = load_groundingdino(
                model_config_path=config_path,
                model_checkpoint_path=checkpoint_path
            )
            self.groundingdino_model.to(self.device)
            print("Grounding DINO loaded successfully")
        except Exception as e:
            print(f"Failed to load Grounding DINO: {e}")
            raise RuntimeError("Grounding DINO initialization failed.")

        # Load SAM
        try:
            sam_checkpoint = "models/SAM/sam_vit_h_4b8939.pth"
            sam = sam_model_registry["vit_h"](checkpoint=sam_checkpoint)
            sam.to(device=self.device)
            self.sam_predictor = SamPredictor(sam)
            print("SAM loaded successfully")
        except Exception as e:
            print(f"Failed to load SAM: {e}")
            raise RuntimeError("SAM initialization failed.")

        # Load CLIPSeg
        try:
            self.clipseg_model = CLIPDensePredT(version='ViT-B/16', reduce_dim=64)
            self.clipseg_model.eval()
            weights_path = 'clipseg/weights/rd64-uni.pth'
            self.clipseg_model.load_state_dict(torch.load(weights_path, map_location=self.device), strict=False)
            self.clipseg_model.to(self.device)
            print("CLIPSeg loaded successfully")
        except Exception as e:
            print(f"Failed to load CLIPSeg: {e}")
            raise RuntimeError("CLIPSeg initialization failed.")

    def Run(self, frame: np.ndarray, options: Any):
        # 1. Determine the text prompt (default to "face")
        prompt = "face"
        if hasattr(options, 'masking_text'):
            prompt = options.masking_text

        # 2. Prepare images
        # image_rgb is for SAM; image_transformed is for Grounding DINO
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image_pil = Image.fromarray(image_rgb)
        
        # Define the transform required by Grounding DINO
        import groundingdino.datasets.transforms as T
        transform = T.Compose([
            T.RandomResize([800], max_size=1333),
            T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        
        # Convert PIL image to the mathematical tensor Grounding DINO expects
        image_transformed, _ = transform(image_pil, None)

        # 3. Grounding DINO: Find the bounding box
        try:
            boxes, logits, phrases = predict(
                model=self.groundingdino_model,
                image=image_transformed, # The tensor goes here
                caption=prompt,
                box_threshold=0.35,
                text_threshold=0.25,
                device=self.device
            )
            if len(boxes) == 0:
                # Return a blank mask if nothing is found
                return np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)
        except Exception as e:
            print(f"Grounding DINO error: {e}")
            return np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)

        # 4. SAM: Turn the box into a high-quality pixel mask
        try:
            self.sam_predictor.set_image(image_rgb)
            
            # Scale the normalized DINO box back to the actual pixel size of your frame
            h, w, _ = frame.shape
            input_box = boxes[0] * np.array([w, h, w, h])
            
            # Generate the mask
            masks, _, _ = self.sam_predictor.predict(
                box=input_box.numpy(), 
                multimask_output=False
            )
            # Convert boolean mask to 0-255 grayscale image
            mask = masks[0].astype(np.uint8) * 255
        except Exception as e:
            print(f"SAM error: {e}")
            return np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)

        # 5. Final Resize to ensure compatibility with the roop-unleashed UI
        mask = cv2.resize(mask, (frame.shape[1], frame.shape[0]))
        return mask

    def Release(self):
        self.groundingdino_model = None
        self.sam_predictor = None
        self.clipseg_model = None
        torch.cuda.empty_cache()
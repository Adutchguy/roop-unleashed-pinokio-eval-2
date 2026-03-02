import torch
from cutie.inference.inference_core import InferenceCore
from cutie.model.cutie import CUTIE
from roop.utilities import get_device
from typing import Any, Dict
import cv2
import numpy as np
import roop.globals

class Video_Cutie:
    processorname = 'video_cutie'
    type = 'video'
    print(f"DEBUG: cutie module was loaded in some capacity)")
    def __init__(self):
        self.cutie_model = None
        self.device = None

    def Initialize(self, options: Dict[str, Any]):
        self.devicename = options['devicename']
        self.device = get_device(self.devicename)
        torch.set_grad_enabled(False)

        # Load Cutie model from the official repo's pretrained weights
        try:
            self.cutie_model = CUTIE().to(self.device)
            checkpoint_path = 'models/Cutie/cutie.pth'
            self.cutie_model.load_state_dict(torch.load(checkpoint_path, map_location=self.device))
            self.cutie_model.eval()
            print("Cutie loaded successfully")
        except Exception as e:
            print(f"Failed to load Cutie: {e}")
            raise RuntimeError("Cutie initialization failed. Check model file and paths.")

    def Run(self, video_frames: list[np.ndarray], initial_mask: np.ndarray):
        if len(video_frames) == 0:
            return []

        # Convert frames to RGB if needed (Cutie expects RGB)
        video_frames_rgb = [cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) if frame.shape[2] == 3 else frame for frame in video_frames]

        # Initial inference on first frame
        try:
            processor = InferenceCore(self.cutie_model, images=np.array(video_frames_rgb[0:1]), num_objects=1)
            processor.interact(initial_mask, frame_idx=0, end_idx=0)
            print("Cutie initial interaction done")
        except Exception as e:
            print(f"Cutie initial interact failed: {e}")
            return []

        # Propagate to all frames
        output_masks = [initial_mask]
        for idx in range(1, len(video_frames_rgb)):
            try:
                mask_prob = processor.step(video_frames_rgb[idx])
                mask = (mask_prob > 0.5).astype(np.uint8) * 255
                output_masks.append(mask)
            except Exception as e:
                print(f"Cutie step failed on frame {idx}: {e}")
                output_masks.append(output_masks[-1])  # Fallback to last mask

        return output_masks

    def Release(self):
        if self.cutie_model is not None:
            del self.cutie_model
        torch.cuda.empty_cache()
        print("Video_Cutie released resources")
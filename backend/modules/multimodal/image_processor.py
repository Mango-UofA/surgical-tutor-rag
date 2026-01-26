"""
Surgical Image Processor
Handles surgical image/video preprocessing and analysis
"""

import cv2
import numpy as np
from PIL import Image
from typing import List, Dict, Any, Union, Tuple, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SurgicalImageProcessor:
    """
    Processes surgical images and video frames for multimodal RAG.
    
    Features:
    - Image quality assessment
    - Frame extraction from surgical videos
    - Image enhancement and preprocessing
    - Anatomical region detection
    """
    
    def __init__(self, target_size: Tuple[int, int] = (224, 224)):
        """
        Initialize image processor.
        
        Args:
            target_size: Target size for processed images
        """
        self.target_size = target_size
        logger.info(f"Initialized SurgicalImageProcessor (target size: {target_size})")
    
    def load_image(self, image_path: Union[str, Path]) -> Image.Image:
        """
        Load and validate surgical image.
        
        Args:
            image_path: Path to image file
        
        Returns:
            PIL Image object
        """
        try:
            img = Image.open(image_path).convert('RGB')
            logger.debug(f"Loaded image: {image_path} ({img.size})")
            return img
        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            raise
    
    def extract_video_frames(self, 
                            video_path: Union[str, Path],
                            fps: Optional[int] = None,
                            max_frames: int = 100) -> List[np.ndarray]:
        """
        Extract frames from surgical video.
        
        Args:
            video_path: Path to video file
            fps: Frames per second to extract (None = use video fps)
            max_frames: Maximum number of frames to extract
        
        Returns:
            List of video frames as numpy arrays
        """
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        # Get video properties
        video_fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Calculate frame interval
        if fps is None:
            frame_interval = 1
        else:
            frame_interval = max(1, int(video_fps / fps))
        
        frames = []
        frame_count = 0
        
        logger.info(f"Extracting frames from {video_path} (FPS: {video_fps}, Total: {total_frames})")
        
        while len(frames) < max_frames:
            ret, frame = cap.read()
            
            if not ret:
                break
            
            if frame_count % frame_interval == 0:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
            
            frame_count += 1
        
        cap.release()
        logger.info(f"Extracted {len(frames)} frames from video")
        
        return frames
    
    def assess_image_quality(self, image: Union[np.ndarray, Image.Image]) -> Dict[str, float]:
        """
        Assess surgical image quality.
        
        Args:
            image: Input image
        
        Returns:
            Quality metrics
        """
        # Convert to numpy if PIL Image
        if isinstance(image, Image.Image):
            image = np.array(image)
        
        # Convert to grayscale for analysis
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Calculate sharpness (Laplacian variance)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Calculate brightness
        brightness = gray.mean()
        
        # Calculate contrast
        contrast = gray.std()
        
        # Simple quality score
        quality_score = min(100, (laplacian_var / 100) * 0.5 + (contrast / 128) * 50)
        
        return {
            'sharpness': float(laplacian_var),
            'brightness': float(brightness),
            'contrast': float(contrast),
            'quality_score': float(quality_score)
        }
    
    def enhance_image(self, image: Image.Image, enhance_contrast: bool = True) -> Image.Image:
        """
        Enhance surgical image quality.
        
        Args:
            image: Input image
            enhance_contrast: Whether to apply contrast enhancement
        
        Returns:
            Enhanced image
        """
        img_array = np.array(image)
        
        if enhance_contrast:
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
            l, a, b = cv2.split(lab)
            
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            lab = cv2.merge([l, a, b])
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        else:
            enhanced = img_array
        
        return Image.fromarray(enhanced)
    
    def detect_roi(self, image: Union[np.ndarray, Image.Image]) -> Dict[str, Any]:
        """
        Detect region of interest in surgical image.
        
        Args:
            image: Surgical image
        
        Returns:
            ROI information
        """
        # Convert to numpy if needed
        if isinstance(image, Image.Image):
            image = np.array(image)
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # Apply Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Detect edges
        edges = cv2.Canny(blurred, 50, 150)
        
        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            # Get largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            return {
                'bbox': (x, y, w, h),
                'area': w * h,
                'center': (x + w // 2, y + h // 2)
            }
        
        return None
    
    def create_thumbnail(self, image: Image.Image, size: Tuple[int, int] = (128, 128)) -> Image.Image:
        """
        Create thumbnail of surgical image.
        
        Args:
            image: Input image
            size: Thumbnail size
        
        Returns:
            Thumbnail image
        """
        thumbnail = image.copy()
        thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
        return thumbnail
    
    def batch_process_images(self, 
                            image_paths: List[Union[str, Path]],
                            enhance: bool = True) -> List[Dict[str, Any]]:
        """
        Process multiple surgical images.
        
        Args:
            image_paths: List of image paths
            enhance: Whether to enhance images
        
        Returns:
            List of processed image data
        """
        results = []
        
        for img_path in image_paths:
            try:
                # Load image
                img = self.load_image(img_path)
                
                # Assess quality
                quality = self.assess_image_quality(img)
                
                # Enhance if requested
                if enhance:
                    img = self.enhance_image(img)
                
                # Create thumbnail
                thumbnail = self.create_thumbnail(img)
                
                results.append({
                    'path': str(img_path),
                    'image': img,
                    'thumbnail': thumbnail,
                    'quality': quality,
                    'size': img.size
                })
                
            except Exception as e:
                logger.error(f"Failed to process {img_path}: {e}")
                continue
        
        logger.info(f"Processed {len(results)}/{len(image_paths)} images successfully")
        return results
    
    def extract_surgical_phases_from_video(self,
                                          video_path: Union[str, Path],
                                          phase_duration: int = 30) -> List[Dict[str, Any]]:
        """
        Extract representative frames for each surgical phase from video.
        
        Args:
            video_path: Path to surgical video
            phase_duration: Approximate duration of each phase in seconds
        
        Returns:
            List of phase frames with metadata
        """
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps
        
        # Estimate number of phases
        num_phases = max(1, int(duration / phase_duration))
        frames_per_phase = total_frames // num_phases
        
        phase_frames = []
        
        for phase_idx in range(num_phases):
            # Jump to middle of phase
            frame_pos = int((phase_idx + 0.5) * frames_per_phase)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
            
            ret, frame = cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                timestamp = frame_pos / fps
                
                phase_frames.append({
                    'phase_index': phase_idx,
                    'frame': frame_rgb,
                    'timestamp': timestamp,
                    'frame_number': frame_pos
                })
        
        cap.release()
        logger.info(f"Extracted {len(phase_frames)} phase frames from video")
        
        return phase_frames

"""
Image storage manager for saving and retrieving surgical images
"""
import os
import json
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
import shutil


class ImageStorageManager:
    """Manages storage of surgical images with metadata"""
    
    def __init__(self, storage_path: str = "./uploaded_images"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.metadata_file = self.storage_path / "metadata.json"
        self._load_metadata()
    
    def _load_metadata(self):
        """Load existing metadata from disk"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}
    
    def _save_metadata(self):
        """Save metadata to disk"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def _generate_image_id(self, image_bytes: bytes) -> str:
        """Generate unique ID from image content hash"""
        return hashlib.sha256(image_bytes).hexdigest()[:16]
    
    def save_image(
        self,
        image_bytes: bytes,
        filename: str,
        procedure: Optional[str] = None,
        quality_score: Optional[float] = None,
        detected_instruments: Optional[List[Dict[str, Any]]] = None,
        surgical_phase: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Save image to filesystem with metadata
        
        Args:
            image_bytes: Raw image bytes
            filename: Original filename
            procedure: Surgical procedure name
            quality_score: Image quality score (0-100)
            detected_instruments: List of detected instruments with confidence
            surgical_phase: Identified surgical phase
            additional_metadata: Any additional metadata
        
        Returns:
            Dictionary with image_id and storage path
        """
        # Generate unique ID
        image_id = self._generate_image_id(image_bytes)
        
        # Create file extension
        ext = Path(filename).suffix or '.jpg'
        image_filename = f"{image_id}{ext}"
        image_path = self.storage_path / image_filename
        
        # Save image file
        with open(image_path, 'wb') as f:
            f.write(image_bytes)
        
        # Create metadata entry
        metadata_entry = {
            "image_id": image_id,
            "filename": image_filename,
            "original_filename": filename,
            "upload_timestamp": datetime.now().isoformat(),
            "file_size": len(image_bytes),
            "procedure": procedure,
            "quality_score": quality_score,
            "detected_instruments": detected_instruments or [],
            "surgical_phase": surgical_phase,
            "file_path": str(image_path)
        }
        
        # Add additional metadata
        if additional_metadata:
            metadata_entry.update(additional_metadata)
        
        # Store metadata
        self.metadata[image_id] = metadata_entry
        self._save_metadata()
        
        return {
            "image_id": image_id,
            "path": str(image_path),
            "metadata": metadata_entry
        }
    
    def get_image(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve image metadata by ID"""
        return self.metadata.get(image_id)
    
    def get_image_bytes(self, image_id: str) -> Optional[bytes]:
        """Retrieve raw image bytes by ID"""
        metadata = self.get_image(image_id)
        if not metadata:
            return None
        
        image_path = Path(metadata["file_path"])
        if not image_path.exists():
            return None
        
        with open(image_path, 'rb') as f:
            return f.read()
    
    def list_images(
        self,
        procedure: Optional[str] = None,
        min_quality: Optional[float] = None,
        phase: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List images with optional filters
        
        Args:
            procedure: Filter by procedure name
            min_quality: Minimum quality score
            phase: Filter by surgical phase
            limit: Maximum number of results
        
        Returns:
            List of image metadata entries
        """
        results = []
        
        for image_id, metadata in self.metadata.items():
            # Apply filters
            if procedure and metadata.get("procedure") != procedure:
                continue
            if min_quality and (metadata.get("quality_score") or 0) < min_quality:
                continue
            if phase and metadata.get("surgical_phase") != phase:
                continue
            
            results.append(metadata)
            
            if len(results) >= limit:
                break
        
        # Sort by upload timestamp (newest first)
        results.sort(key=lambda x: x["upload_timestamp"], reverse=True)
        
        return results
    
    def delete_image(self, image_id: str) -> bool:
        """Delete image and its metadata"""
        metadata = self.get_image(image_id)
        if not metadata:
            return False
        
        # Delete file
        image_path = Path(metadata["file_path"])
        if image_path.exists():
            image_path.unlink()
        
        # Remove metadata
        del self.metadata[image_id]
        self._save_metadata()
        
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get storage statistics"""
        total_images = len(self.metadata)
        total_size = sum(m.get("file_size", 0) for m in self.metadata.values())
        
        procedures = {}
        phases = {}
        instruments = {}
        
        for metadata in self.metadata.values():
            # Count procedures
            proc = metadata.get("procedure")
            if proc:
                procedures[proc] = procedures.get(proc, 0) + 1
            
            # Count phases
            phase = metadata.get("surgical_phase")
            if phase:
                phases[phase] = phases.get(phase, 0) + 1
            
            # Count instruments
            for inst in metadata.get("detected_instruments", []):
                inst_name = inst.get("name")
                if inst_name:
                    instruments[inst_name] = instruments.get(inst_name, 0) + 1
        
        return {
            "total_images": total_images,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "procedures": procedures,
            "phases": phases,
            "instruments": instruments,
            "storage_path": str(self.storage_path)
        }

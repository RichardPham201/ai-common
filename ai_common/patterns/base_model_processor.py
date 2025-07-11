"""Base processor class with common patterns"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from ..utils.gpu_memory_utils import GPUMemoryUtils


class BaseModelProcessor(ABC):
    """
    Abstract base class for AI processors implementing common patterns:
    - Singleton pattern
    - Lazy loading
    - GPU memory management
    - Model lifecycle management
    """
    
    _instances = {}
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern per class"""
        if cls not in cls._instances:
            cls._instances[cls] = super(BaseModelProcessor, cls).__new__(cls)
        return cls._instances[cls]
    
    def __init__(self, lazy_load_model: bool = True, logger: Optional[logging.Logger] = None):
        """
        Initialize base processor
        
        Args:
            lazy_load_model: Whether to use lazy loading for models
            logger: Optional logger instance
        """
        # Prevent re-initialization in singleton
        if hasattr(self, '_initialized'):
            return
            
        self.lazy_load_model = lazy_load_model
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.device = self._get_device()
        self.model = None
        self._initialized = True
        
        self.logger.info(f"{self.__class__.__name__} initialized on device: {self.device}")
    
    def _get_device(self) -> str:
        """Get the best available device"""
        if TORCH_AVAILABLE and torch.cuda.is_available():
            return "cuda"
        return "cpu"
    
    @abstractmethod
    def _load_model(self, model_path: str, **kwargs):
        """
        Load the model from file
        
        Args:
            model_path: Path to model file
            **kwargs: Additional model loading parameters
            
        Returns:
            Loaded model
        """
        pass
    
    def _ensure_model_loaded(self, model_path: str, **kwargs):
        """
        Ensure model is loaded for inference
        
        Args:
            model_path: Path to model file
            **kwargs: Additional model loading parameters
        """
        if self.model is None:
            self.logger.info(f"Loading model from: {model_path}")
            GPUMemoryUtils.log_gpu_memory_usage(self.logger, "Before loading")
            
            self.model = self._load_model(model_path, **kwargs)
            
            GPUMemoryUtils.log_gpu_memory_usage(self.logger, "After loading")
    
    def _offload_model(self):
        """Offload model to free memory"""
        if self.model is not None:
            self.logger.info("Offloading model to free memory")
            GPUMemoryUtils.log_gpu_memory_usage(self.logger, "Before offload")
            
            # Move model to CPU and delete
            GPUMemoryUtils.offload_model(self.model, self.logger)
            del self.model
            self.model = None
            
            GPUMemoryUtils.clear_gpu_memory(self.logger)
            GPUMemoryUtils.log_gpu_memory_usage(self.logger, "After offload")
    
    def is_model_loaded(self) -> bool:
        """Check if model is currently loaded"""
        return self.model is not None
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get current model and system status"""
        return {
            'model_loaded': self.is_model_loaded(),
            'lazy_load_enabled': self.lazy_load_model,
            'device': self.device,
            'gpu_memory': GPUMemoryUtils.get_gpu_memory_usage()
        }
    
    def force_offload_model(self):
        """Force offload model immediately"""
        self._offload_model()
    
    def force_clear_gpu_memory(self):
        """Force clear all GPU memory"""
        self.logger.info("Force clearing all GPU memory")
        
        GPUMemoryUtils.log_gpu_memory_usage(self.logger, "Before force clear")
        
        # Offload model first
        self._offload_model()
        
        # Additional aggressive cleanup
        GPUMemoryUtils.clear_gpu_memory(self.logger)
        
        GPUMemoryUtils.log_gpu_memory_usage(self.logger, "After force clear")
        
        gpu_status = GPUMemoryUtils.get_gpu_memory_usage()
        if gpu_status and gpu_status['allocated'] > 0.1:  # Still more than 100MB
            self.logger.warning("GPU memory still not fully cleared!")
            self.logger.info("You may need to restart the Python process to fully clear GPU memory")
    
    @abstractmethod
    def process(self, input_data, **kwargs):
        """
        Main processing method to be implemented by subclasses
        
        Args:
            input_data: Input data to process
            **kwargs: Additional processing parameters
            
        Returns:
            Processed output
        """
        pass
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup resources"""
        if self.lazy_load_model:
            self._offload_model()
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        try:
            if hasattr(self, 'model') and self.model is not None:
                self._offload_model()
        except Exception:
            pass  # Ignore errors during cleanup

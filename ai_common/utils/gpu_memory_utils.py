"""GPU Memory monitoring and management utilities"""

import gc
import logging
from typing import Optional, Dict, Any

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class GPUMemoryUtils:
    """Utilities for GPU memory monitoring and management"""
    
    @staticmethod
    def get_gpu_memory_usage() -> Optional[Dict[str, Any]]:
        """
        Get current GPU memory usage information
        
        Returns:
            Dictionary with memory usage info or None if CUDA not available
            Format: {
                'allocated': float,  # GB allocated
                'reserved': float,   # GB reserved
                'device': str        # Device name
            }
        """
        if not TORCH_AVAILABLE:
            return None
            
        if torch.cuda.is_available():
            try:
                return {
                    'allocated': torch.cuda.memory_allocated() / (1024**3),  # Convert to GB
                    'reserved': torch.cuda.memory_reserved() / (1024**3),    # Convert to GB
                    'device': torch.cuda.get_device_name(0)
                }
            except Exception as e:
                logging.warning(f"Error getting GPU memory usage: {str(e)}")
                return None
        return None
    
    @staticmethod
    def clear_gpu_memory(logger: Optional[logging.Logger] = None) -> None:
        """
        Clear GPU memory cache
        
        Args:
            logger: Optional logger instance for debugging
        """
        if not TORCH_AVAILABLE:
            return
            
        log = logger or logging.getLogger(__name__)
        
        if torch.cuda.is_available():
            try:
                gpu_before = GPUMemoryUtils.get_gpu_memory_usage()
                if gpu_before and logger:
                    log.info(f"GPU Memory before clear - Allocated: {gpu_before['allocated']:.2f}GB, Reserved: {gpu_before['reserved']:.2f}GB")
                
                # Force garbage collection and clear CUDA cache
                gc.collect()
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                
                gpu_after = GPUMemoryUtils.get_gpu_memory_usage()
                if gpu_after and logger:
                    log.info(f"GPU Memory after clear - Allocated: {gpu_after['allocated']:.2f}GB, Reserved: {gpu_after['reserved']:.2f}GB")
                    
            except Exception as e:
                log.warning(f"Error clearing GPU memory: {str(e)}")
    
    @staticmethod
    def log_gpu_memory_usage(logger: logging.Logger, prefix: str = "") -> None:
        """
        Log current GPU memory usage
        
        Args:
            logger: Logger instance
            prefix: Optional prefix for log message
        """
        gpu_status = GPUMemoryUtils.get_gpu_memory_usage()
        if gpu_status:
            prefix_str = f"{prefix} " if prefix else ""
            logger.info(f"{prefix_str}GPU Memory - Allocated: {gpu_status['allocated']:.2f}GB, "
                       f"Reserved: {gpu_status['reserved']:.2f}GB, Device: {gpu_status['device']}")
        else:
            logger.info(f"{prefix}GPU not available or CUDA not installed")
    
    @staticmethod
    def move_model_to_device(model, device: str, logger: Optional[logging.Logger] = None):
        """
        Safely move model to specified device
        
        Args:
            model: PyTorch model to move
            device: Target device ('cuda', 'cpu', etc.)
            logger: Optional logger instance
            
        Returns:
            Model moved to device
        """
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch not available")
            
        log = logger or logging.getLogger(__name__)
        
        try:
            if device == 'cuda' and not torch.cuda.is_available():
                log.warning("CUDA requested but not available, using CPU")
                device = 'cpu'
                
            model = model.to(device)
            log.info(f"Model moved to device: {device}")
            return model
            
        except Exception as e:
            log.error(f"Error moving model to device {device}: {str(e)}")
            raise
    
    @staticmethod
    def offload_model(model, logger: Optional[logging.Logger] = None) -> None:
        """
        Offload model from GPU to free memory
        
        Args:
            model: PyTorch model to offload
            logger: Optional logger instance
        """
        if not TORCH_AVAILABLE:
            return
            
        log = logger or logging.getLogger(__name__)
        
        try:
            gpu_before = GPUMemoryUtils.get_gpu_memory_usage()
            if gpu_before and logger:
                log.info(f"GPU Memory before offload - Allocated: {gpu_before['allocated']:.2f}GB")
            
            # Move model to CPU
            if torch.cuda.is_available() and hasattr(model, 'cpu'):
                model.cpu()
                
            # Clear GPU cache
            GPUMemoryUtils.clear_gpu_memory(logger)
            
            gpu_after = GPUMemoryUtils.get_gpu_memory_usage()
            if gpu_after and logger:
                log.info(f"GPU Memory after offload - Allocated: {gpu_after['allocated']:.2f}GB")
                
        except Exception as e:
            log.error(f"Error offloading model: {str(e)}")
            raise

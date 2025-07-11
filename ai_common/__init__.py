"""AI Common Package

Common utilities and services for AI projects.
"""

__version__ = "1.0.0"
__author__ = "AI Team"

# Import main components
from .queue.queue_service import QueueService
from .queue.rabbitmq_service import RabbitMQService
from .utils.gpu_memory_utils import GPUMemoryUtils
from .utils.image_utils import ImageUtils
from .patterns.base_model_processor import BaseModelProcessor

__all__ = [
    "QueueService",
    "RabbitMQService", 
    "GPUMemoryUtils",
    "ImageUtils",
    "BaseModelProcessor"
]

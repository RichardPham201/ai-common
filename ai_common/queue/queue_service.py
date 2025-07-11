"""Abstract queue service interface"""

from abc import ABC, abstractmethod
from typing import Callable


class QueueService(ABC):
    """Abstract base class for queue services"""

    @abstractmethod
    def publish(self, queue_name: str, payload: dict) -> None:
        """
        Publish a message to the specified queue
        
        Args:
            queue_name: Name of the queue to publish to
            payload: Message payload as dictionary
        """
        pass

    @abstractmethod
    def register_consumer(self, queue_name: str, handler: Callable[[dict], None]) -> None:
        """
        Register a consumer handler for the specified queue
        
        Args:
            queue_name: Name of the queue to consume from
            handler: Callback function to handle incoming messages
        """
        pass
    
    @abstractmethod
    def close_connection(self) -> None:
        """Close the connection to the queue service"""
        pass

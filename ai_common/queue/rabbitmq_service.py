"""RabbitMQ implementation of QueueService"""

import pika
import json
import logging
import ssl
from typing import Callable, Optional
from .queue_service import QueueService


class RabbitMQService(QueueService):
    """RabbitMQ implementation of the queue service"""
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: int = 5672, 
                 virtual_host: str = "/", 
                 username: str = "guest", 
                 password: str = "guest",
                 use_tls: bool = False,
                 ca_cert_path: Optional[str] = None,
                 cert_path: Optional[str] = None,
                 key_path: Optional[str] = None,
                 verify_hostname: bool = False,
                 logger: Optional[logging.Logger] = None):
        """
        Initialize RabbitMQ service
        
        Args:
            host: RabbitMQ server host
            port: RabbitMQ server port (default: 5672 for non-TLS, 5671 for TLS)
            virtual_host: Virtual host name
            username: Username for authentication
            password: Password for authentication
            use_tls: Enable TLS/SSL connection
            ca_cert_path: Path to CA certificate file (for TLS)
            cert_path: Path to client certificate file (for TLS with client auth)
            key_path: Path to client private key file (for TLS with client auth)
            verify_hostname: Whether to verify hostname in TLS connection
            logger: Optional logger instance
        """
        self.host = host
        # Default to TLS port if TLS is enabled and port is default
        if use_tls and port == 5672:
            self.port = 5671
        else:
            self.port = port
        self.virtual_host = virtual_host
        self.use_tls = use_tls
        self.ca_cert_path = ca_cert_path
        self.cert_path = cert_path
        self.key_path = key_path
        self.verify_hostname = verify_hostname
        self.credentials = pika.PlainCredentials(username, password)
        
        # Configure SSL context if TLS is enabled
        ssl_context = None
        if self.use_tls:
            ssl_context = ssl.create_default_context()
            
            # Load CA certificate if provided
            if self.ca_cert_path:
                ssl_context.load_verify_locations(cafile=self.ca_cert_path)
            
            # Load client certificate and key if provided
            if self.cert_path and self.key_path:
                ssl_context.load_cert_chain(self.cert_path, self.key_path)
            
            # Configure hostname verification
            if not self.verify_hostname:
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
        
        self.connection_params = pika.ConnectionParameters(
            host=self.host,
            port=self.port,
            virtual_host=self.virtual_host,
            credentials=self.credentials,
            ssl_options=pika.SSLOptions(ssl_context) if ssl_context else None
        )
        self.logger = logger or logging.getLogger(__name__)
        self._connection = None
        
    def _get_connection(self):
        """Get or create a connection to RabbitMQ"""
        if self._connection is None or self._connection.is_closed:
            self._connection = pika.BlockingConnection(self.connection_params)
        return self._connection

    def publish(self, queue_name: str, payload: dict) -> None:
        """
        Publish a message to the specified queue
        
        Args:
            queue_name: Name of the queue to publish to
            payload: Message payload as dictionary
        """
        try:
            connection = pika.BlockingConnection(self.connection_params)
            channel = connection.channel()
            
            # Declare queue with durability
            channel.queue_declare(queue=queue_name, durable=True)
            
            # Publish message with persistence
            channel.basic_publish(
                exchange="",
                routing_key=queue_name,
                body=json.dumps(payload),
                properties=pika.BasicProperties(delivery_mode=2)  # Make message persistent
            )
            
            connection.close()
            self.logger.info(f"Message published to queue '{queue_name}'")
            
        except Exception as e:
            self.logger.error(f"Error publishing message to queue '{queue_name}': {str(e)}")
            raise

    def register_consumer(self, queue_name: str, handler: Callable[[dict], None]) -> None:
        """
        Register a consumer handler for the specified queue
        
        Args:
            queue_name: Name of the queue to consume from
            handler: Callback function to handle incoming messages
        """
        try:
            connection = pika.BlockingConnection(self.connection_params)
            channel = connection.channel()
            
            # Declare queue with durability
            channel.queue_declare(queue=queue_name, durable=True)
            
            # Set QoS to process one message at a time
            channel.basic_qos(prefetch_count=1)

            def callback(ch, method, properties, body):
                """Internal callback wrapper"""
                try:
                    # Parse message body
                    data = json.loads(body)
                    
                    # Call user handler
                    handler(data)
                    
                    # Acknowledge message on success
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    self.logger.debug(f"Message processed successfully from queue '{queue_name}'")
                    
                except json.JSONDecodeError as e:
                    self.logger.error(f"Error parsing JSON message from queue '{queue_name}': {str(e)}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
                    
                except Exception as e:
                    self.logger.error(f"Error handling message from queue '{queue_name}': {str(e)}")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

            # Register consumer
            channel.basic_consume(queue=queue_name, on_message_callback=callback)
            
            self.logger.info(f"Waiting for messages in queue '{queue_name}'. To exit press CTRL+C")
            channel.start_consuming()
            
        except KeyboardInterrupt:
            self.logger.info("Consumer interrupted by user")
            channel.stop_consuming()
            connection.close()
            
        except Exception as e:
            self.logger.error(f"Error setting up consumer for queue '{queue_name}': {str(e)}")
            raise

    def close_connection(self) -> None:
        """Close the connection to RabbitMQ"""
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            self.logger.info("RabbitMQ connection closed")
            
    def __del__(self):
        """Destructor to ensure connection is closed"""
        self.close_connection()

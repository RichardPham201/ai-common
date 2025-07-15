"""RabbitMQ implementation of QueueService"""

import pika
import json
import logging
import ssl
import threading
import functools
from typing import Callable, Optional, Dict
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
                 heartbeat: int = 30,
                 blocked_connection_timeout: int = 300,
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
            heartbeat: Heartbeat interval in seconds (default: 30)
            blocked_connection_timeout: Timeout for blocked connections in seconds (default: 300)
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
            ssl_options=pika.SSLOptions(ssl_context) if ssl_context else None,
            heartbeat=heartbeat,
            blocked_connection_timeout=blocked_connection_timeout
        )
        self.logger = logger or logging.getLogger(__name__)
        self._connection = None
        self._consumers = {}  # Store consumer threads
        self._consumer_threads = []  # Store thread references
        self._stop_consuming = False
        
        # Log heartbeat configuration
        self.logger.info(f"RabbitMQ service initialized with heartbeat={heartbeat}s, blocked_timeout={blocked_connection_timeout}s")
        
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
        Each consumer will run in its own thread with its own connection
        
        Args:
            queue_name: Name of the queue to consume from
            handler: Callback function to handle incoming messages
        """
        if queue_name in self._consumers:
            self.logger.warning(f"Consumer for queue '{queue_name}' already registered. Skipping.")
            return
            
        # Store consumer info
        self._consumers[queue_name] = handler
        
        # Create and start consumer thread
        consumer_thread = threading.Thread(
            target=self._run_consumer,
            args=(queue_name, handler),
            daemon=True,
            name=f"Consumer-{queue_name}"
        )
        self._consumer_threads.append(consumer_thread)
        consumer_thread.start()
        
        self.logger.info(f"Consumer registered and started for queue '{queue_name}'")

    def _run_consumer(self, queue_name: str, handler: Callable[[dict], None]) -> None:
        """
        Run consumer in its own thread with its own connection
        
        Args:
            queue_name: Name of the queue to consume from
            handler: Callback function to handle incoming messages
        """
        try:
            # Create dedicated connection for this consumer
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
            
            self.logger.info(f"Consumer started for queue '{queue_name}' in thread {threading.current_thread().name}")
            
            # Start consuming in this thread
            while not self._stop_consuming:
                try:
                    connection.process_data_events(time_limit=1)  # Process events with timeout
                except Exception as e:
                    if not self._stop_consuming:
                        self.logger.error(f"Error in consumer for queue '{queue_name}': {str(e)}")
                        break
            
            # Cleanup
            channel.stop_consuming()
            connection.close()
            self.logger.info(f"Consumer stopped for queue '{queue_name}'")
            
        except Exception as e:
            self.logger.error(f"Error setting up consumer for queue '{queue_name}': {str(e)}")

    def start_consuming_all(self) -> None:
        """
        Start consuming from all registered queues
        This is a blocking call that keeps the main thread alive
        """
        if not self._consumer_threads:
            self.logger.warning("No consumers registered")
            return
            
        self.logger.info(f"Started {len(self._consumer_threads)} consumers")
        
        try:
            # Keep main thread alive while consumers run
            while not self._stop_consuming:
                import time
                time.sleep(1)
                
                # Check if any consumer threads have died
                for thread in self._consumer_threads:
                    if not thread.is_alive():
                        self.logger.warning(f"Consumer thread {thread.name} died")
                        
        except KeyboardInterrupt:
            self.logger.info("Stopping all consumers...")
            self.stop_consuming()

    def stop_consuming(self) -> None:
        """Stop all consumers"""
        self._stop_consuming = True
        
        # Wait for all consumer threads to finish
        for thread in self._consumer_threads:
            if thread.is_alive():
                thread.join(timeout=5)
                
        self.logger.info("All consumers stopped")

    def close_connection(self) -> None:
        """Close all connections and stop consumers"""
        self.stop_consuming()
        
        if self._connection and not self._connection.is_closed:
            self._connection.close()
            self.logger.info("RabbitMQ connection closed")
            
    def __del__(self):
        """Destructor to ensure connections are closed"""
        self.close_connection()

    def _ack_message(self, connection, channel, delivery_tag):
        """
        Acknowledge message using connection callback (thread-safe)
        Based on pika's threaded consumer pattern
        """
        if channel.is_open:
            channel.basic_ack(delivery_tag)
        else:
            # Channel is already closed, log it
            self.logger.warning(f"Cannot ACK message {delivery_tag}: channel is closed")
    
    def _nack_message(self, connection, channel, delivery_tag, requeue=False):
        """
        Negative acknowledge message using connection callback (thread-safe)
        """
        if channel.is_open:
            channel.basic_nack(delivery_tag, requeue=requeue)
        else:
            # Channel is already closed, log it
            self.logger.warning(f"Cannot NACK message {delivery_tag}: channel is closed")
    
    def _process_message_threaded(self, connection, channel, delivery_tag, body, handler):
        """
        Process message in a separate thread and safely acknowledge
        This prevents blocking the consumer thread
        """
        thread_id = threading.get_ident()
        try:
            # Parse message body
            data = json.loads(body)
            
            # Call user handler
            handler(data)
            
            # Acknowledge message safely using connection callback
            ack_callback = functools.partial(self._ack_message, connection, channel, delivery_tag)
            connection.add_callback_threadsafe(ack_callback)
            
            self.logger.debug(f"Message processed successfully in thread {thread_id}, delivery_tag: {delivery_tag}")
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing JSON message in thread {thread_id}: {str(e)}")
            nack_callback = functools.partial(self._nack_message, connection, channel, delivery_tag, False)
            connection.add_callback_threadsafe(nack_callback)
            
        except Exception as e:
            self.logger.error(f"Error handling message in thread {thread_id}: {str(e)}")
            nack_callback = functools.partial(self._nack_message, connection, channel, delivery_tag, False)
            connection.add_callback_threadsafe(nack_callback)

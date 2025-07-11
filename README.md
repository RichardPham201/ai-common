# AI Common

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Common utilities and services for AI projects, providing shared functionality for queue management, GPU memory monitoring, image processing, and AI model patterns.

## Features

- **Queue Services**: Abstract queue interface with RabbitMQ implementation
- **GPU Memory Management**: Automatic memory monitoring and cleanup utilities
- **Image Processing**: Format conversions, base64 encoding, PIL/OpenCV utilities  
- **AI Model Patterns**: Base processor class with singleton, lazy loading, and resource management

## Installation

### From Git (Recommended)

```bash
pip install git+https://github.com/RichardPham201/ai-common.git
```

### Development Installation

```bash
git clone https://github.com/RichardPham201/ai-common.git
cd ai-common
pip install -e .
```

## Quick Start

### Queue Services

```python
from ai_common.queue import RabbitMQService

# Initialize RabbitMQ service
queue_service = RabbitMQService(host="localhost")

# Publish message
queue_service.publish("my_queue", {"task": "process_image", "image_id": "123"})

# Register consumer
def handle_message(data):
    print(f"Processing: {data}")

queue_service.register_consumer("my_queue", handle_message)
```

### GPU Memory Management

```python
from ai_common.utils import GPUMemoryUtils

# Monitor GPU memory
gpu_info = GPUMemoryUtils.get_gpu_memory_usage()
print(f"GPU Memory: {gpu_info['allocated']:.2f}GB allocated")

# Clear GPU memory
GPUMemoryUtils.clear_gpu_memory()

# Log memory usage
import logging
logger = logging.getLogger(__name__)
GPUMemoryUtils.log_gpu_memory_usage(logger, "Before processing")
```

### Image Processing

```python
from ai_common.utils import ImageUtils
from PIL import Image

# Convert image to base64
base64_str = ImageUtils.image_to_base64("image.jpg")

# Convert base64 back to PIL Image  
pil_image = ImageUtils.base64_to_image(base64_str)

# Convert between formats
cv2_image = ImageUtils.pil_to_cv2(pil_image)
numpy_array = ImageUtils.pil_to_numpy(pil_image)
```

### AI Model Processor Pattern

```python
from ai_common.patterns import BaseProcessor

class MyAIProcessor(BaseProcessor):
    def _load_model(self, model_path, **kwargs):
        # Your model loading logic
        model = load_your_model(model_path)
        return model
    
    def process(self, input_data, **kwargs):
        # Ensure model is loaded
        self._ensure_model_loaded("/path/to/model")
        
        # Your processing logic
        result = self.model.predict(input_data)
        
        # Automatic cleanup if lazy loading enabled
        return result

# Usage
processor = MyAIProcessor(lazy_load_model=True)
result = processor.process(my_data)
```

## Requirements

- Python 3.8+
- PyTorch (optional, for GPU utilities)
- Pillow (optional, for image processing)
- OpenCV (optional, for image processing)
- NumPy (optional, for image processing)
- pika (optional, for RabbitMQ)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Changelog

### v1.0.0 (2025-07-11)
- Initial release
- Queue services with RabbitMQ implementation
- GPU memory management utilities
- Image processing utilities
- Base AI processor pattern with singleton and lazy loading

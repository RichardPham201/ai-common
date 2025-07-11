from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-common",
    version="1.0.0",
    description="Common utilities and services for AI projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="AI Team",
    author_email="your-email@example.com",
    url="https://github.com/RichardPham201/ai-common",
    packages=find_packages(),
    install_requires=[
        # Core dependencies - always installed
    ],
    extras_require={
        "gpu": ["torch>=1.9.0", "torchvision>=0.10.0"],
        "image": ["pillow>=8.0.0", "numpy>=1.21.0"],
        "opencv": ["opencv-python>=4.5.0"],
        "queue": ["pika>=1.2.0"],
        "all": [
            "torch>=1.9.0", 
            "torchvision>=0.10.0",
            "pillow>=8.0.0", 
            "numpy>=1.21.0",
            "opencv-python>=4.5.0",
            "pika>=1.2.0"
        ]
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="ai, machine learning, gpu, image processing, queue, utilities",
    project_urls={
        "Bug Reports": "https://github.com/RichardPham201/ai-common/issues",
        "Source": "https://github.com/RichardPham201/ai-common",
        "Documentation": "https://github.com/RichardPham201/ai-common#readme",
    },
)

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="superpowers",
    version="1.0.0",
    author="obra",
    description="An agentic skills framework & software development methodology",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/obra/superpowers",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pydantic>=2.0",
        "typing-extensions>=4.0",
    ],
    extras_require={
        "dev": [
            "pytest",
            "black",
            "mypy",
        ],
    },
)

from setuptools import setup, find_packages

setup(
    name="mkdocs-protobuf-plugin",
    version="0.3.1",
    description="MkDocs plugin to convert protobuf files to markdown",
    author="MkDocs Protobuf Plugin Developer",
    author_email="example@example.com",
    url="https://github.com/yourusername/mkdocs-protobuf-plugin",
    packages=find_packages(),
    install_requires=[
        "mkdocs>=1.4.0",
        "watchdog>=2.1.0",
    ],
    entry_points={
        "mkdocs.plugins": [
            "protobuf = mkdocs_protobuf_plugin:ProtobufPlugin",
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)

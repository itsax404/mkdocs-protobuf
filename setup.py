from setuptools import setup, find_packages


setup(
    name="mkdocs-proto-gen",  # Required
    version="2.0.0",  # Required
    description="MkDocs plugin to convert protobuf files to markdown",  # Optional
    url="https://github.com/itsax404/mkdocs-protobuf",  # Optional
    author="itsax404",  # Optional
    author_email="itsax404@gmail.com",  # Optional
    classifiers=[  # Optional
        "Classifier: Development Status :: 4 - Beta",
        "Classifier: Intended Audience :: Developers",
        "Classifier: License :: OSI Approved :: MIT License",
        "Classifier: Programming Language :: Python"
    ],
    keywords="sample, setuptools, development",  # Optional
    packages=find_packages(),  # Required
    python_requires=">=3.8",
    install_requires=[
        "mkdocs>=1.4.0",
        "watchdog>=2.1.0",
    ], # Optional
    extras_require={  # Optional
        "test": ["unittest"],
    },
    entry_points={
        "mkdocs.plugins": [
            "protobuf = mkdocs_protobuf_plugin:ProtobufPlugin",
        ]
    },
)

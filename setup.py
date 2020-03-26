from setuptools import setup

test_deps = ["pytest", "pytest-asyncio", "pytest-cov", "packaging"]

setup(
    name="aiocouch",
    version="1.0.0",
    license="BSD 3-clause",
    description="🛋 An asynchronous client library for CouchDB 2.x",
    author="TU Dresden",
    url="https://github.com/metricq/aiocouch",
    keywords=["asyncio", "couchdb"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    python_requires=">=3.6",
    packages=["aiocouch"],
    scripts=[],
    install_requires=["aiohttp~=3.0"],
    setup_requires=["pytest-runner"],
    tests_require=test_deps,
    extras_require={
        "examples": ["aiomonitor", "click", "click-log", "click-completion"],
        "tests": test_deps,
    },
)

from setuptools import setup

test_deps = ["pytest", "pytest-asyncio", "pytest-cov"]

setup(
    name="aiocouch",
    version="0.0",
    author="TU Dresden",
    python_requires=">=3.6",
    packages=["aiocouch"],
    scripts=[],
    install_requires=["aiohttp"],
    setup_requires=["pytest-runner"],
    tests_require=test_deps,
    extras_require={
        "examples": ["aiomonitor", "click", "click-log", "click-completion"],
        "tests": test_deps,
    },
)

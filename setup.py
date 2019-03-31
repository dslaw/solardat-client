from setuptools import setup


setup(
    name="solardat",
    author="David Law",
    author_email="davidsamuellaw@gmail.com",
    license="MIT",
    install_requires=[
        "lxml",
        "requests",
    ],
    packages=["solardat"],
    package_data={"solardat": ["resources/*"]},
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Science/Research",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)

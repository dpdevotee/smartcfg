from setuptools import setup

with open("README.md") as file:
    read_me_description = file.read()

setup(
    name='smartcfg',
    version='0.0.1',
    py_modules=['smartcfg'],
    long_description=read_me_description,
    long_description_content_type="text/markdown",
    install_requires=['PyYAML'],
)

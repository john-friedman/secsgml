from setuptools import setup, find_packages
import os

# Read the contents of your README file
with open(os.path.join(os.path.dirname(__file__), '../readme.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="secsgml",
    version="0.0.2",
    packages=find_packages(),
    install_requires=[
    ],
    description="Parse Securities and Exchange Commission Standard Generalized Markup Language (SEC SGML) files",
    long_description=long_description,
    long_description_content_type='text/markdown',
)
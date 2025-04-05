from setuptools import setup, Extension
from pathlib import Path
import platform
import os
import sys
from setuptools import find_packages

# Handle the Cython dependency - we'll require it to be installed first
# This block will attempt to import Cython, and if it's not available,
# it will temporarily install it for the duration of the build
import subprocess
import importlib.util

# Check if Cython is installed
cython_available = importlib.util.find_spec("Cython") is not None

# If Cython is not installed, install it temporarily
if not cython_available:
    print("Cython not found, installing temporarily for build...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "cython>=0.29.24"])
    
# Now Cython should be available
from Cython.Build import cythonize

# Platform-specific settings
include_dirs = []
library_dirs = []
# Only add Windows paths if on Windows
if platform.system() == "Windows":
    sdk_paths = [
        r"C:\Program Files (x86)\Windows Kits\10\Include\10.0.22621.0\ucrt",
        r"C:\Program Files (x86)\Windows Kits\10\Include\10.0.22621.0\shared",
        r"C:\Program Files (x86)\Windows Kits\10\Include\10.0.22621.0\um"
    ]
    lib_paths = [
        r"C:\Program Files (x86)\Windows Kits\10\Lib\10.0.22621.0\um\x64",
        r"C:\Program Files (x86)\Windows Kits\10\Lib\10.0.22621.0\ucrt\x64"
    ]
    include_dirs = [path for path in sdk_paths if os.path.exists(path)]
    library_dirs = [path for path in lib_paths if os.path.exists(path)]

# Read the contents of your README file
try:
    readme_path = Path(__file__).parent.parent / "readme.md"
    with open(readme_path, encoding='utf-8') as f:
        long_description = f.read()
except FileNotFoundError:
    long_description = "# secsgml\nParse Securities and Exchange Commission Standard Generalized Markup Language (SEC SGML) files"

# Define extensions with .pyx files
extensions = [
    Extension(
        "secsgml.uu_decode_cy",
        ["secsgml/uu_decode_cy.pyx"],  # Updated path
        include_dirs=include_dirs,
        library_dirs=library_dirs,
    ),
    Extension(
        "secsgml.sgml_memory_cy",
        ["secsgml/sgml_memory_cy.pyx"],  # Updated path
        include_dirs=include_dirs,
        library_dirs=library_dirs,
    ),
]

# Cython compiler directives
cython_directives = {
    'language_level': "3",
    'boundscheck': False,
    'wraparound': False,
    'initializedcheck': False,
    'cdivision': True,
}

# Apply cythonize
extensions = cythonize(
    extensions,
    compiler_directives=cython_directives,
    annotate=True
)

setup(
    name="secsgml",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[],
    setup_requires=[
        'cython>=0.29.24',
    ],
    package_data={
        "secsgml": ["*.pyx", "*.c"],  # Include both .pyx and generated .c files
    },
    ext_modules=extensions,
    description="Parse Securities and Exchange Commission Standard Generalized Markup Language (SEC SGML) files",
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="MIT",
    author="John Friedman",
    author_email="johnfriedman@datamule.xyz"
)
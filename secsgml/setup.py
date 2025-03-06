from setuptools import setup, Extension
from pathlib import Path
import platform
import os
from setuptools import find_packages
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

# Define Cython extension with compiler directives
extensions = [
    Extension(
        "secsgml.uu_decode_cy",
        ["secsgml/uu_decode_cy.pyx"],
        include_dirs=include_dirs,
        library_dirs=library_dirs,
    ),
    Extension(
        "secsgml.sgml_memory_cy",
        ["secsgml/sgml_memory_cy.pyx"],
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

setup(
    name="secsgml",
    version="0.0.7",
    packages=find_packages(),
    install_requires=[
    ],
    setup_requires=[
        'cython',
    ],
    ext_modules=cythonize(
        extensions,
        compiler_directives=cython_directives,
        annotate=True
    ),
    description="Parse Securities and Exchange Commission Standard Generalized Markup Language (SEC SGML) files",
    long_description=long_description,
    long_description_content_type='text/markdown',
)
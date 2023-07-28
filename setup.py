
from setuptools import setup
from uscmdrelay.info import APP_NAME, APP_VERSION, APP_DESCRIPTION, APP_AUTHOR, APP_AUTHOR_EMAIL, APP_AUTHOR_URL

with open("README.md", "r") as f:
    long_description = f.read()

with open("requirements.txt") as f:
    requirements = [line.strip() for line in f]

setup(
    name=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="GPLv3",
    author=APP_AUTHOR,
    author_email=APP_AUTHOR_EMAIL,
    author_url=APP_AUTHOR_URL,
    python_requires='>=3.9',
    install_requires=requirements,
    packages=[
        'uscmdrelay',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        'Operating System :: POSIX :: Linux',
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Utilities",
    ],
    entry_points={
        'console_scripts': [
            'uscmdrelay = uscmdrelay:main',
        ],
    },
)
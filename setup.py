import multiprocessing  # noqa

from setuptools import setup, find_packages

requirements = []
with open('requirements.txt', 'r') as in_:
    requirements = in_.readlines()

setup(
    name='myfitnesspal',
    version='1.9',
    url='http://github.com/coddingtonbear/python-myfitnesspal/',
    description='Access health and fitness data stored in Myfitnesspal',
    author='Adam Coddington',
    author_email='me@adamcoddington.net',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],
    packages=find_packages(),
    install_requires=requirements,
    test_suite='nose.collector',
    tests_require=[
        'nose',
        'mock',
    ],
    entry_points={
        'console_scripts': [
            'myfitnesspal = myfitnesspal.cmdline:main'
        ]
    },
)

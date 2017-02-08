#!/usr/bin/env python

from setuptools import setup

dependencies = ['hyper>=0.7']

try:
    # noinspection PyUnresolvedReferences
    import enum
except ImportError:
    dependencies.append('enum34')

setup(
    name='apns2',
    version='0.2.0',
    packages=['apns2'],
    install_requires=dependencies,
    url='https://github.com/Pr0Ger/PyAPNs2',
    license='MIT',
    author='Sergey Petrov',
    author_email='me@pr0ger.prg',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries',
    ],
    description='A python library for interacting with the Apple Push Notification Service via HTTP/2 protocol'
)

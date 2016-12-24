#!/usr/bin/env python

from distutils.core import setup

dependencies = ['hyper']

try:
    # noinspection PyUnresolvedReferences
    import enum
except ImportError:
    dependencies.append('enum34')

setup(
    name='apns2',
    version='0.1.3',
    packages=['apns2'],
    install_requires=dependencies,
    url='https://github.com/Pr0Ger/PyAPNs2',
    license='MIT',
    author='Sergey Petrov',
    author_email='me@pr0ger.prg',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries',
    ],
    description='A python library for interacting with the Apple Push Notification Service via HTTP/2 protocol'
)

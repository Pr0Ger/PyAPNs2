#!/usr/bin/env python

from distutils.core import setup

dependencies = ['PyJWT', 'future']

try:
    # noinspection PyUnresolvedReferences
    import enum
except ImportError:
    dependencies.append('enum34')

setup(
    name='apns2',
    version='0.1.7',
    packages=['apns2'],
    install_requires=dependencies,
    url='https://github.com/anscii/PyAPNs2',
    license='MIT',
    author='Natalya Akentyeva',
    author_email='nt.aknt@gmail.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries',
    ],
    description='A python library for interacting with the Apple Push Notification Service via HTTP/2 protocol'
)

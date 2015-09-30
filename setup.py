#!/usr/bin/env python
from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='pyTelegramBotAPI',
      version='0.3.7',
      description='Python Telegram bot api. ',
      long_description=readme(),
      author='eternnoir',
      author_email='eternnoir@gmail.com',
      url='https://github.com/eternnoir/pyTelegramBotAPI',
      packages=['telebot'],
      license='GPL2',
      keywords='telegram bot api tools',
      install_requires=['pytest', 'requests', 'six'],
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Environment :: Console',
          'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
      ]
      )

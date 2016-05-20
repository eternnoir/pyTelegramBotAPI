#!/usr/bin/env python
from setuptools import setup
from io import open

def readme():
    with open('README.rst', encoding='utf-8') as f:
        return f.read()

setup(name='pyTelegramBotAPI',
      version='2.1.2',
      description='Python Telegram bot api. ',
      long_description=readme(),
      author='eternnoir',
      author_email='eternnoir@gmail.com',
      url='https://github.com/eternnoir/pyTelegramBotAPI',
      packages=['telebot'],
      license='GPL2',
      keywords='telegram bot api tools',
      install_requires=['requests', 'six'],
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

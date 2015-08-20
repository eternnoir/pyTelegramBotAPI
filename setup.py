#!/usr/bin/env python
from setuptools import setup

setup(name='pyTelegramBotAPI',
      version='0.3.1',
      description='Python Telegram bot api. ',
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

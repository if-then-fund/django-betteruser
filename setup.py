# Note to self: To upload a new version to PyPI, run:
# python3 setup.py sdist upload

from setuptools import setup, find_packages

setup(
  name='django-betteruser',
  version='0.1.0',
  author=u'Joshua Tauberer',
  author_email=u'jt@occams.info',
  packages=find_packages(),
  url='https://github.com/if-then-fund/django-betteruser',
  license='CC0 (copyright waived)',
  description='A better User model and helper functions for Django 1.7+.',
  long_description=open("README.rst").read(),
  keywords="Django User model",
  install_requires=["email_validator==0.1.0-rc1"],
)

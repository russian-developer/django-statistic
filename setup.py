from setuptools import setup, find_packages
from setuptools.command.test import test


class TestCommand(test):
    def run(self):
        from tests.runtests import runtests
        runtests()


setup(
    name='django-statistic',
    version='1.0',
    description='Statistic for django models',
    long_description=open('README.md').read(),
    author='Constantin Slednev',
    author_email='c.slednev@gmail.com',
    license='BSD',
    url='https://github.com/unk2k/django-statistic',
    packages=find_packages(),
    include_package_data=True,
    platforms='any',
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Framework :: Django',
    ],
)


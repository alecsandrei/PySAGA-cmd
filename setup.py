from setuptools import setup, find_packages


VERSION = '0.0.2'
DESCRIPTION = 'A package that allows you to run SAGA GIS tools in a Python environment.'
LONG_DESCRIPTION = 'A package that allows you to run SAGA GIS tools in a Python environment by running terminal commands.'

setup(
    name='PySAGA-cmd',
    version=VERSION,
    author='Cuvuliuc Alex-Andrei',
    author_email="<cuvuliucalexandrei@gmail.com>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='https://github.com/alecsandrei/PySAGA-cmd',
    packages=find_packages(),
    install_requires=[],
    keywords=['python', 'gis', 'SAGA GIS', 'saga_cmd', 'PySAGA'],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3',
        'Operating System :: Unix',
        'Operating System :: Microsoft :: Windows',
    ],
    extras_require={
        'dev': ['twine >=4.0.2'],
    },
)

from setuptools import setup, find_packages
setup(
    name='bitcart-async',
    packages=find_packages(),
    version='0.2.5',
    license='MIT',
    description='Bitcart coins support library',
    long_description=open("README.md").read(),
    long_description_content_type='text/markdown',
    author='MrNaif2018',
    author_email='chuff184@gmail.com',
    url='https://github.com/MrNaif2018/bitcart-sdk/',
    keywords=['electrum', ' daemon', 'bitcart', 'asyncio'],
    install_requires=[
        'aiohttp',
        'simplejson'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
)

from setuptools import setup, find_packages
setup(
  name = 'bitcart',  
  packages = find_packages(),
  version = '0.1.2',    
  license='MIT',       
  description = 'Bitcart coins support library',
  long_description = open("README.md").read(),
  author = 'MrNaif2018',               
  author_email = 'chuff184@gmail.com',      
  url = 'https://github.com/MrNaif2018/bitcart-sdk/',  
  download_url = 'https://github.com/MrNaif2018/bitcart-sdk/archive/0.1.tar.gz',   
  keywords = ['electrum',' daemon', 'bitcart'], 
  install_requires=[        
          'requests',
          'simplejson'
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',   

    'Intended Audience :: Developers',     
    'Topic :: Software Development :: Build Tools',

    'License :: OSI Approved :: MIT License',

    'Programming Language :: Python :: 3',   
    'Programming Language :: Python :: 3.4',
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
  ],
)

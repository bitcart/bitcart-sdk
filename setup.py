from setuptools import find_packages, setup


def main() -> None:
    setup(
        name="bitcart",
        packages=find_packages(),
        version="1.1.0.0",
        license="MIT",
        description="BitcartCC coins support library",
        long_description=open("README.md").read(),
        long_description_content_type="text/markdown",
        author="MrNaif2018",
        author_email="chuff184@gmail.com",
        url="https://github.com/bitcartcc/bitcart-sdk",
        keywords=["electrum", "daemon", "bitcart", "bitcartcc"],
        install_requires=["jsonrpcclient[aiohttp]", "aiohttp<4.0.0"],
        extras_require={"proxy": ["aiohttp_socks"]},
        classifiers=[
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Topic :: Software Development :: Build Tools",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.6",
            "Programming Language :: Python :: 3.7",
            "Programming Language :: Python :: 3.8",
        ],
    )


if __name__ == "__main__":
    main()

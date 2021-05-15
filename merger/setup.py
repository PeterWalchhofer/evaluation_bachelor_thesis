from setuptools import setup, find_packages

setup(
    name='merger',
    version='0.1.1',
    author='Peter Walchhofer',
    packages=["cli"],
    description='Merging and enrichment by building on ftm.',
    install_requires=[
        "followthemoney>=2.1.9",
        "click>=7.1.2",
        #"pyicu>=2.6"
    ],
    entry_points = {
     "console_scripts":[
          "merger = cli.merger:cli",
     ]
    }
)

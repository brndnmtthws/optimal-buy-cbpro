from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

setup(
    name='optimal_buy_gdax',
    version='1.1.5',
    description='Buy the coins, optimally!',
    long_description=readme,
    long_description_content_type="text/markdown",
    author='Brenden Matthews',
    author_email='brenden@diddyinc.com',
    url='https://github.com/brndnmtthws/optimal-buy-gdax',
    packages=find_packages(exclude=('tests', 'docs')),
    entry_points={
        'console_scripts':
            ['optimal-buy-gdax=optimal_buy_gdax.optimal_buy_gdax:main'],
    },
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: Public Domain",
        "Operating System :: OS Independent",
    ),
)

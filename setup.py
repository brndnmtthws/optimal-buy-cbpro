from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='optimal_buy_gdax',
    version='1.1.2',
    description='Buy the coins, optimally!',
    long_description=readme,
    author='Brenden Matthews',
    author_email='brenden@diddyinc.com',
    url='https://github.com/brndnmtthws/optimal-buy-gdax',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    entry_points={
        'console_scripts':
            ['optimal-buy-gdax=optimal_buy_gdax.optimal_buy_gdax:main'],
    },
)

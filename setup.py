from setuptools import setup, find_packages

with open('README.md') as f:
    readme = f.read()

setup(
    name='optimal_buy_cbpro',
    version='1.1.6',
    description='Buy the coins, optimally!',
    long_description=readme,
    long_description_content_type="text/markdown",
    author='Brenden Matthews',
    author_email='brenden@diddyinc.com',
    url='https://github.com/brndnmtthws/optimal-buy-cbpro',
    packages=find_packages(),
    entry_points={
        'console_scripts':
            ['optimal-buy-cbpro=optimal_buy_cbpro.optimal_buy_cbpro:main'],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Public Domain",
        "Operating System :: OS Independent",
    ],
)

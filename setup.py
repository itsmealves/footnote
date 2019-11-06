"""footnote - setup.py"""
import footnote
import setuptools


VERSION = footnote.__version__
LONG_DESC = open('README.md').read()

setuptools.setup(
    name="footnote",
    version=VERSION,
    author="Gabriel Alves",
    long_description=LONG_DESC,
    author_email="gabriel.alves@pickcells.bio",
    long_description_content_type="text/markdown",
    description="Patches your code comments into logging calls",
    keywords="logging,comment,patch,monkey",
    license="MIT",
    url="https://github.com/itsmealves/footnote",
    classifiers=[],
    packages=[
        'footnote',
    ],
    install_requires=[],
    python_requires=">=3.5",
    test_suite="tests",
    include_package_data=True,
    zip_safe=False)
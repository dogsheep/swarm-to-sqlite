from setuptools import setup
import os

VERSION = "0.3.2"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="swarm-to-sqlite",
    description="Create a SQLite database containing your checkin history from Foursquare Swarm",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Simon Willison",
    url="https://github.com/dogsheep/swarm-to-sqlite",
    project_urls={
        "Issues": "https://github.com/dogsheep/swarm-to-sqlite/issues",
        "CI": "https://github.com/dogsheep/swarm-to-sqlite/actions",
        "Changelog": "https://github.com/dogsheep/swarm-to-sqlite/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["swarm_to_sqlite"],
    entry_points="""
        [console_scripts]
        swarm-to-sqlite=swarm_to_sqlite.cli:cli
    """,
    install_requires=["sqlite-utils>=2.4.4", "click", "requests"],
    extras_require={"test": ["pytest"]},
    tests_require=["swarm-to-sqlite[test]"],
)

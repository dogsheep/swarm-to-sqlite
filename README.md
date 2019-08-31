# swarm-to-sqlite

[![PyPI](https://img.shields.io/pypi/v/swarm-to-sqlite.svg)](https://pypi.org/project/swarm-to-sqlite/)
[![CircleCI](https://circleci.com/gh/dogsheep/swarm-to-sqlite.svg?style=svg)](https://circleci.com/gh/dogsheep/swarm-to-sqlite)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/dogsheep/swarm-to-sqlite/blob/master/LICENSE)

Create a SQLite database containing your checkin history from Foursquare Swarm.

## How to install

    $ pip install swarm-to-sqlite

## Usage

You will need to first obtain a valid OAuth token for your Foursquare account. You can do so using this tool: https://your-foursquare-oauth-token.glitch.me/

Simplest usage is to simply provide the name of the database file you wish to write to. The tool will prompt you to paste in your token, and will then download your checkins and store them in the specified database file.

    $ swarm-to-sqlite checkins.db
    Please provide your Foursquare OAuth token:
    Importing 3699 checkins  [#########-----------------------] 27% 00:02:31

You can also pass the token as a command-line option:

    $ swarm-to-sqlite checkins.db --token=XXX

Or as an environment variable:

    $ export FOURSQUARE_TOKEN=XXX
    $ swarm-to-sqlite checkins.db

In addition to saving the checkins to a database, you can also write them to a JSON file using the `--save` option:

    $ swarm-to-sqlite checkins.db --save=checkins.json

Having done this, you can re-import checkins directly from that file (rather than making API calls to fetch data from Foursquare) like this:

    $ swarm-to-sqlite checkins.db --load=checkins.json

## Using with Datasette

The SQLite database produced by this tool is designed to be browsed using [Datasette](https://datasette.readthedocs.io/).

You can install the [datasette-cluster-map](https://github.com/simonw/datasette-cluster-map) plugin to view your checkins on a map.

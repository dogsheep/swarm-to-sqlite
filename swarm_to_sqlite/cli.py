import click
import os
import json
import sqlite_utils
from .utils import save_checkin, ensure_foreign_keys, create_views


@click.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.option("-t", "--token", help="Foursquare OAuth token")
@click.option("-f", "--file", help="Path to JSON file on disk")
@click.option("-s", "--silent", is_flag=True, help="Don't show progress bar")
def cli(db_path, token, file, silent):
    "Save Swarm checkins to a SQLite database"
    if not ((token or file) and not (token and file)):
        raise click.ClickException("Provide either --file or --token")

    if token:
        checkins = fetch_all_checkins(token, count_first=True)
        checkin_count = next(checkins)
    else:
        checkins = json.load(open(file))
        checkin_count = len(checkins)
    db = sqlite_utils.Database(db_path)
    if silent:
        for checkin in checkins:
            save_checkin(checkin, db)
    else:
        with click.progressbar(
            length=checkin_count,
            label="Importing {} checkin{}".format(
                checkin_count, "" if checkin_count == 1 else "s"
            ),
        ) as bar:
            for checkin in checkins:
                save_checkin(checkin, db)
                bar.update(1)
    ensure_foreign_keys(db)
    create_views(db)

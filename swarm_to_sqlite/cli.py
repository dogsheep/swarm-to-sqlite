import click
import os
import json
import sqlite_utils
from .utils import save_checkin, ensure_foreign_keys, create_views, fetch_all_checkins


@click.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.option("-t", "--token", help="Foursquare OAuth token")
@click.option("--load", help="Load checkins from this JSON file on disk")
@click.option("--save", help="Save checkins to this JSON file on disk")
@click.option("-s", "--silent", is_flag=True, help="Don't show progress bar")
def cli(db_path, token, load, save, silent):
    "Save Swarm checkins to a SQLite database"
    if token and load:
        raise click.ClickException("Provide either --load or --token")

    if not token and not load:
        token = click.prompt(
            "Please provide your Foursquare OAuth token", hide_input=True
        )

    if token:
        checkins = fetch_all_checkins(token, count_first=True)
        checkin_count = next(checkins)
    else:
        checkins = json.load(open(load))
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

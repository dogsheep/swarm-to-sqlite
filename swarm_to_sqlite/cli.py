import click
import os
import json
import re
import sqlite_utils
from .utils import save_checkin, ensure_foreign_keys, create_views, fetch_all_checkins


since_re = re.compile("^(\d+)(w|h|d)$")


def validate_since(ctx, param, value):
    if value:
        match = since_re.match(value)
        if not match:
            raise click.BadParameter("since need to be in format 3d/2h/1w")
        num, unit = match.groups()
        multiplier = {"d": 24 * 60 * 60, "h": 60 * 60, "w": 7 * 24 * 60 * 60}[unit]
        return int(num) * multiplier


@click.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.option("--token", envvar="FOURSQUARE_TOKEN", help="Foursquare OAuth token")
@click.option(
    "--load", type=click.File(), help="Load checkins from this JSON file on disk"
)
@click.option(
    "--save", type=click.File("w"), help="Save checkins to this JSON file on disk"
)
@click.option(
    "--since",
    type=str,
    callback=validate_since,
    help="Look for checkins since 1w/2d/3h ago",
)
@click.option("-s", "--silent", is_flag=True, help="Don't show progress bar")
def cli(db_path, token, load, save, since, silent):
    "Save Swarm checkins to a SQLite database"
    if token and load:
        raise click.ClickException("Provide either --load or --token")

    if not token and not load:
        token = click.prompt(
            "Please provide your Foursquare OAuth token", hide_input=True
        )

    if token:
        checkins = fetch_all_checkins(token, count_first=True, since_delta=since)
        checkin_count = next(checkins)
    else:
        checkins = json.load(load)
        checkin_count = len(checkins)
    db = sqlite_utils.Database(db_path)
    saved = []
    if silent:
        for checkin in checkins:
            save_checkin(checkin, db)
            if save:
                saved.append(checkin)
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
                if save:
                    saved.append(checkin)
    ensure_foreign_keys(db)
    create_views(db)
    if save:
        json.dump(saved, save)

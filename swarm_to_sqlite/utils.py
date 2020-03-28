import datetime
import time
import requests
from sqlite_utils.db import AlterError, ForeignKey


def save_checkin(checkin, db):
    # Create copy that we can modify
    checkin = dict(checkin)
    if "venue" in checkin:
        venue = checkin.pop("venue")
        categories = venue.pop("categories")
        venue.update(venue.pop("location"))
        venue.pop("labeledLatLngs", None)
        venue["latitude"] = venue.pop("lat")
        venue["longitude"] = venue.pop("lng")
        v = db["venues"].insert(venue, pk="id", alter=True, replace=True)
        for category in categories:
            cleanup_category(category)
            v.m2m("categories", category, pk="id")
        checkin["venue"] = venue["id"]
    else:
        checkin["venue"] = None
    if "createdBy" not in checkin:
        checkin["createdBy"] = None
    if "event" in checkin:
        event = checkin.pop("event")
        categories = event.pop("categories")
        e = db["events"].insert(event, pk="id", alter=True, replace=True)
        for category in categories:
            cleanup_category(category)
            e.m2m("categories", category, pk="id")
        checkin["event"] = event["id"]
    else:
        checkin["event"] = None

    if "sticker" in checkin:
        sticker = checkin.pop("sticker")
        sticker_image = sticker.pop("image")
        sticker["image_prefix"] = sticker_image["prefix"]
        sticker["image_sizes"] = sticker_image["sizes"]
        sticker["image_name"] = sticker_image["name"]
        checkin["sticker"] = (
            db["stickers"].insert(sticker, pk="id", alter=True, replace=True).last_pk
        )
    else:
        checkin["sticker"] = None

    checkin["created"] = datetime.datetime.utcfromtimestamp(
        checkin["createdAt"]
    ).isoformat()
    checkin["source"] = db["sources"].lookup(checkin["source"])
    users_with = checkin.pop("with", None) or []
    users_likes = []
    for group in checkin["likes"]["groups"]:
        users_likes.extend(group["items"])
    del checkin["likes"]
    photos = checkin.pop("photos")["items"]
    posts = (checkin.pop("posts") or {}).get("items") or []
    if checkin.get("createdBy"):
        created_by_user = checkin.pop("createdBy")
        cleanup_user(created_by_user)
        db["users"].insert(created_by_user, pk="id", replace=True)
        checkin["createdBy"] = created_by_user["id"]
    checkin["comments_count"] = checkin.pop("comments")["count"]
    # Actually save the checkin
    checkins_table = db["checkins"].insert(
        checkin,
        pk="id",
        foreign_keys=(("venue", "venues", "id"), ("source", "sources", "id")),
        alter=True,
        replace=True,
    )
    # Save m2m 'with' users and 'likes' users
    for user in users_with:
        cleanup_user(user)
        checkins_table.m2m("users", user, m2m_table="with", pk="id")
    for user in users_likes:
        cleanup_user(user)
        checkins_table.m2m("users", user, m2m_table="likes", pk="id")
    # Handle photos
    photos_table = db.table("photos", pk="id", foreign_keys=("user", "source"))
    for photo in photos:
        photo["created"] = datetime.datetime.utcfromtimestamp(
            photo["createdAt"]
        ).isoformat()
        photo["source"] = db["sources"].lookup(photo["source"])
        user = photo.pop("user")
        cleanup_user(user)
        db["users"].insert(user, pk="id", replace=True)
        photo["user"] = user["id"]
        photos_table.insert(photo, replace=True)
    # Handle posts
    posts_table = db.table("posts", pk="id")
    for post in posts:
        post["created"] = datetime.datetime.utcfromtimestamp(
            post["createdAt"]
        ).isoformat()
        post["post_source"] = (
            db["post_sources"].insert(post.pop("source"), pk="id", replace=True).last_pk
        )
        post["checkin"] = checkin["id"]
        posts_table.insert(post, foreign_keys=("post_source", "checkin"), replace=True)


def cleanup_user(user):
    photo = user.pop("photo", None) or {}
    user["photo_prefix"] = photo.get("prefix")
    user["photo_suffix"] = photo.get("suffix")


def cleanup_category(category):
    category["icon_prefix"] = category["icon"]["prefix"]
    category["icon_suffix"] = category["icon"]["suffix"]
    del category["icon"]


def ensure_foreign_keys(db):
    existing = []
    for table in db.tables:
        existing.extend(table.foreign_keys)
    desired = [
        ForeignKey(
            table="checkins", column="createdBy", other_table="users", other_column="id"
        ),
        ForeignKey(
            table="checkins", column="event", other_table="events", other_column="id"
        ),
        ForeignKey(
            table="checkins",
            column="sticker",
            other_table="stickers",
            other_column="id",
        ),
    ]
    for fk in desired:
        if fk not in existing:
            try:
                db[fk.table].add_foreign_key(fk.column, fk.other_table, fk.other_column)
            except AlterError:
                pass


def create_views(db):
    for name, sql in (
        (
            "venue_details",
            """
select
    min(created) as first,
    max(created) as last,
    count(venues.id) as count,
    group_concat(distinct categories.name) as venue_categories,
    venues.*
from venues
    join checkins on checkins.venue = venues.id
    join categories_venues on venues.id = categories_venues.venues_id
    join categories on categories.id = categories_venues.categories_id
group by venues.id
        """,
        ),
        (
            "checkin_details",
            """
select
    checkins.id,
    created,
    venues.id as venue_id,
    venues.name as venue_name,
    venues.latitude,
    venues.longitude,
    group_concat(categories.name) as venue_categories,
    shout,
    createdBy,
    events.name as event_name
from checkins
    join venues on checkins.venue = venues.id
    left join events on checkins.event = events.id
    join categories_venues on venues.id = categories_venues.venues_id
    join categories on categories.id = categories_venues.categories_id
group by checkins.id
order by createdAt desc
        """,
        ),
    ):
        try:
            db.create_view(name, sql)
        except Exception:
            pass


def fetch_all_checkins(token, count_first=False, since_delta=None):
    # Generator that yields all checkins using the provided OAuth token
    # If count_first is True it first yields the total checkins count
    before_timestamp = None
    params = {
        "oauth_token": token,
        "v": "20190101",
        "sort": "newestfirst",
        "limit": "250",
    }
    if since_delta:
        params["afterTimestamp"] = int(time.time() - since_delta)
    first = True
    while True:
        if before_timestamp is not None:
            params["beforeTimestamp"] = before_timestamp
        url = "https://api.foursquare.com/v2/users/self/checkins"
        data = requests.get(url, params).json()
        if first:
            first = False
            if count_first:
                yield data["response"]["checkins"]["count"]
        if not data.get("response", {}).get("checkins", {}).get("items"):
            break
        for item in data["response"]["checkins"]["items"]:
            yield item
        before_timestamp = item["createdAt"]

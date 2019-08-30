from swarm_to_sqlite import utils
import pytest
import json
import sqlite_utils
from sqlite_utils.db import ForeignKey
import pathlib


def load_checkin():
    json_path = pathlib.Path(__file__).parent / "checkin.json"
    return json.load(open(json_path, "r"))


@pytest.fixture(scope="session")
def converted():
    db = sqlite_utils.Database(":memory:")
    utils.save_checkin(load_checkin(), db)
    return db


def test_tables(converted):
    assert {
        "venues",
        "categories",
        "with",
        "users",
        "likes",
        "categories_venues",
        "sources",
        "checkins",
        "photos",
        "categories_events",
        "events",
        "posts",
        "post_sources",
    } == set(converted.table_names())


def test_venue(converted):
    venue = list(converted["venues"].rows)[0]
    assert {
        "id": "453774dcf964a520bd3b1fe3",
        "name": "Restaurant Name",
        "address": "Address",
        "crossStreet": "at cross street",
        "postalCode": "94xxx",
        "cc": "US",
        "city": "City",
        "state": "State",
        "country": "Country",
        "formattedAddress": '["Address (at cross street)", "City, State, Zip", "Country"]',
        "latitude": 38.456,
        "longitude": -122.345,
    } == venue
    # Venue categories
    categories = list(
        converted["categories"].rows_where(
            "id in (select categories_id from categories_venues where venues_id = '453774dcf964a520bd3b1fe3')"
        )
    )
    assert [
        {
            "id": "4bf58dd8d48988d10c941735",
            "name": "Category Name",
            "pluralName": "Category Names",
            "shortName": "Category",
            "icon_prefix": "https://ss3.4sqi.net/img/categories_v2/food/french_",
            "icon_suffix": ".png",
            "primary": 1,
        }
    ] == categories


def test_event(converted):
    event = list(converted["events"].rows)[0]
    assert {"id": "5bf8e4fb646e38002c472397", "name": "A movie"} == event
    categories = list(
        converted["categories"].rows_where(
            "id in (select categories_id from categories_events where events_id = '5bf8e4fb646e38002c472397')"
        )
    )
    assert [
        {
            "id": "4dfb90c6bd413dd705e8f897",
            "name": "Movie",
            "pluralName": "Movies",
            "shortName": "Movie",
            "primary": 1,
            "icon_prefix": "https://ss3.4sqi.net/img/categories_v2/arts_entertainment/movietheater_",
            "icon_suffix": ".png",
        }
    ] == categories


def test_likes(converted):
    likes = list(converted["likes"].rows)
    assert [
        {"users_id": "314", "checkins_id": "592b2cfe09e28339ac543fde"},
        {"users_id": "323", "checkins_id": "592b2cfe09e28339ac543fde"},
        {"users_id": "778", "checkins_id": "592b2cfe09e28339ac543fde"},
    ] == likes


def test_with_(converted):
    with_ = list(converted["with"].rows)
    assert [{"users_id": "900", "checkins_id": "592b2cfe09e28339ac543fde"}] == with_


def test_users(converted):
    users = list(converted["users"].rows)
    assert [
        {
            "id": "900",
            "firstName": "Natalie",
            "lastName": "Downe",
            "gender": "female",
            "relationship": "friend",
            "photo_prefix": "https://fastly.4sqi.net/img/user/",
            "photo_suffix": "/nd.jpg",
        },
        {
            "id": "314",
            "firstName": "J",
            "lastName": "T",
            "gender": "female",
            "relationship": "friend",
            "photo_prefix": "https://fastly.4sqi.net/img/user/",
            "photo_suffix": "/jt.jpg",
        },
        {
            "id": "323",
            "firstName": "A",
            "lastName": "R",
            "gender": "male",
            "relationship": "friend",
            "photo_prefix": "https://fastly.4sqi.net/img/user/",
            "photo_suffix": "/ar.png",
        },
        {
            "id": "778",
            "firstName": "J",
            "lastName": None,
            "gender": "none",
            "relationship": "friend",
            "photo_prefix": "https://fastly.4sqi.net/img/user/",
            "photo_suffix": "/j",
        },
        {
            "id": "15889193",
            "firstName": "Simon",
            "lastName": "Willison",
            "gender": "male",
            "relationship": "self",
            "photo_prefix": "https://fastly.4sqi.net/img/user/",
            "photo_suffix": "/CNGFSAMX00DB4DYZ.jpg",
        },
    ] == users


def test_photos(converted):
    assert [
        ForeignKey(
            table="photos", column="user", other_table="users", other_column="id"
        ),
        ForeignKey(
            table="photos", column="source", other_table="sources", other_column="id"
        ),
    ] == converted["photos"].foreign_keys
    photos = list(converted["photos"].rows)
    assert [
        {
            "id": "5b3840f34a7aae002c7845ee",
            "createdAt": "2018-07-01T04:48:19",
            "source": 1,
            "prefix": "https://fastly.4sqi.net/img/general/",
            "suffix": "/15889193_ptDsf3Go3egIPU6WhwC4lIsEQLpW5SXxY3J1YyTY7Wc.jpg",
            "width": 1920,
            "height": 1440,
            "visibility": "public",
            "user": "15889193",
        },
        {
            "id": "5b38417b16fa04002c718f84",
            "createdAt": "2018-07-01T04:50:35",
            "source": 1,
            "prefix": "https://fastly.4sqi.net/img/general/",
            "suffix": "/15889193_GrExrA5SoKhYBK6VhZ0g97Zy8qcEdqLpuUCJSTxzaWI.jpg",
            "width": 1920,
            "height": 1440,
            "visibility": "public",
            "user": "15889193",
        },
        {
            "id": "5b38417d04d1ae002c53b844",
            "createdAt": "2018-07-01T04:50:37",
            "source": 1,
            "prefix": "https://fastly.4sqi.net/img/general/",
            "suffix": "/15889193__9cPZDE4Y1dhNgrqueMSFYnv20k4u1hHiqPxw5m3JOc.jpg",
            "width": 1920,
            "height": 1440,
            "visibility": "public",
            "user": "15889193",
        },
    ] == photos


def test_posts(converted):
    assert [
        ForeignKey(
            table="posts", column="checkin", other_table="checkins", other_column="id"
        ),
        ForeignKey(
            table="posts",
            column="post_source",
            other_table="post_sources",
            other_column="id",
        ),
    ] == converted["posts"].foreign_keys
    posts = list(converted["posts"].rows)
    assert [
        {
            "id": "58994045e386e304939156e0",
            "createdAt": "2017-02-07T04:34:29",
            "text": "The samosa chaat appetizer (easily enough for two or even four people) was a revelation - I've never tasted anything quite like it before, absolutely delicious. Chicken tika masala was amazing too.",
            "url": "https://foursquare.com/item/58994045668af77dae50b376",
            "contentId": "58994045668af77dae50b376",
            "post_source": "UJXJTUHR42CKGO54KXQWGUZJL3OJKMKMVHGJ1SWIOC5TRKAC",
            "checkin": "592b2cfe09e28339ac543fde",
        }
    ] == posts


def test_checkin_with_no_event():
    checkin = load_checkin()
    # If no event in checkin, event column should be None
    del checkin["event"]
    db = sqlite_utils.Database(":memory:")
    utils.save_checkin(checkin, db)
    assert 1 == db["checkins"].count
    row = list(db["checkins"].rows)[0]
    assert row["event"] is None

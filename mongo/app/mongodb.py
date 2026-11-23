import os
from pymongo import MongoClient, ASCENDING, DESCENDING

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB", "assignment2")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB_NAME]
patrons_col = db["patrons"]


def _flatten_doc(doc):
    return {
        "patron_id": doc["patron_id"],
        "patron_type": doc.get("patron_type", {}).get("definition"),
        "home_library": doc.get("home_library", {}).get("definition"),
        "notification": doc.get("notification", {}).get("definition"),
        "age_range": doc.get("age_range"),
        "checkouts": doc.get("checkouts"),
        "renewals": doc.get("renewals"),
        "year_registered": doc.get("year_registered"),
    }


def fetch_patrons(limit=50, offset=0, search_id=None):
    if search_id is not None:
        doc = patrons_col.find_one({"patron_id": search_id}, {"_id": 0})
        return [_flatten_doc(doc)] if doc else []

    cursor = (
        patrons_col.find({}, {"_id": 0})
        .sort("patron_id", ASCENDING)
        .skip(offset)
        .limit(limit)
    )
    return [_flatten_doc(doc) for doc in cursor]


def fetch_lookup_options():
    raw_pts = patrons_col.distinct("patron_type")
    raw_libs = patrons_col.distinct("home_library")
    raw_notifs = patrons_col.distinct("notification")

    patron_types = sorted(
        [(d["code"], d["definition"]) for d in raw_pts if d.get("code") is not None],
        key=lambda x: str(x[0]),
    )
    libraries = sorted(
        [(d["code"], d["definition"]) for d in raw_libs if d.get("code") is not None],
        key=lambda x: str(x[1]),
    )
    notifications = sorted(
        [(d["code"], d["definition"]) for d in raw_notifs if d.get("code") is not None],
        key=lambda x: str(x[1]),
    )
    return patron_types, libraries, notifications


def _build_embedded_fields(pt_code, lib_code, notif_code, age_range, checkouts, renewals, year_reg):
    """Resolves definitions from existing documents so embedded sub-documents stay consistent."""
    pt_doc = patrons_col.find_one({"patron_type.code": pt_code}, {"patron_type": 1, "_id": 0})
    lib_doc = patrons_col.find_one({"home_library.code": lib_code}, {"home_library": 1, "_id": 0})
    notif_doc = patrons_col.find_one({"notification.code": notif_code}, {"notification": 1, "_id": 0})

    return {
        "patron_type": pt_doc["patron_type"] if pt_doc else {"code": pt_code, "definition": str(pt_code)},
        "home_library": lib_doc["home_library"] if lib_doc else {"code": lib_code, "definition": str(lib_code)},
        "notification": notif_doc["notification"] if notif_doc else {"code": notif_code, "definition": str(notif_code)},
        "age_range": age_range,
        "checkouts": checkouts,
        "renewals": renewals,
        "year_registered": year_reg,
    }


def insert_patron(pt_code, lib_code, notif_code, age_range, checkouts, renewals, year_reg):
    last_doc = patrons_col.find_one(sort=[("patron_id", DESCENDING)], projection={"patron_id": 1, "_id": 0})
    new_id = (last_doc["patron_id"] + 1) if last_doc else 1

    new_doc = {"patron_id": new_id}
    new_doc.update(_build_embedded_fields(pt_code, lib_code, notif_code, age_range, checkouts, renewals, year_reg))

    patrons_col.insert_one(new_doc)
    return new_id


def update_patron(patron_id, pt_code, lib_code, notif_code, age_range, checkouts, renewals, year_reg):
    updated_fields = _build_embedded_fields(pt_code, lib_code, notif_code, age_range, checkouts, renewals, year_reg)
    patrons_col.update_one({"patron_id": patron_id}, {"$set": updated_fields})


def delete_patron(patron_id):
    patrons_col.delete_one({"patron_id": patron_id})


if __name__ == "__main__":
    pts, libs, notifs = fetch_lookup_options()
    print(f"Loaded {len(pts)} patron types, {len(libs)} libraries, {len(notifs)} notification types.")

    sample = fetch_patrons(limit=3)
    for row in sample:
        print(row)
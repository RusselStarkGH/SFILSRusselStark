import os
import mysql.connector
from pymongo import MongoClient, ASCENDING

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", 3307)),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", "135956"),
    "database": os.getenv("MYSQL_DATABASE", "assignment1"),
}

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB", "assignment2")
BATCH_SIZE = 10000

def migrate():
    mysql_conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = mysql_conn.cursor(dictionary=True, buffered=False)

    mongo_client = MongoClient(MONGO_URI)
    mongo_db = mongo_client[MONGO_DB_NAME]
    patrons_col = mongo_db["patrons"]

    patrons_col.drop()

    sql = """
        SELECT
            s.patron_id,
            s.`Patron Type Code\npatron_type_code` AS pt_code,
            pt.patron_type_definition AS pt_def,
            s.`Home Library Code\nhome_library_code` AS lib_code,
            l.library_definition AS lib_def,
            s.`Notification Preference Code\nnotification_medium_code` AS notif_code,
            n.notification_definition AS notif_def,
            s.`Age Range` AS age_range,
            s.`Total Checkouts\ncheckout_total` AS checkouts,
            s.`Total Renewals\nrenewal_total` AS renewals,
            s.`Year Patron Registered` AS year_registered
        FROM sfpldata s
        LEFT JOIN patron_type pt
            ON s.`Patron Type Code\npatron_type_code` = pt.patron_type_code
        LEFT JOIN library l
            ON s.`Home Library Code\nhome_library_code` = l.library_code
        LEFT JOIN notification n
            ON s.`Notification Preference Code\nnotification_medium_code` = n.notification_code
        ORDER BY s.patron_id ASC
    """

    print("Streaming rows from MySQL and inserting into MongoDB...")
    cursor.execute(sql)

    batch = []
    total_inserted = 0

    for row in cursor:
        doc = {
            "patron_id": row["patron_id"],
            "patron_type": {
                "code": row["pt_code"],
                "definition": row["pt_def"],
            },
            "home_library": {
                "code": row["lib_code"],
                "definition": row["lib_def"],
            },
            "notification": {
                "code": row["notif_code"],
                "definition": row["notif_def"],
            },
            "age_range": row["age_range"],
            "checkouts": row["checkouts"],
            "renewals": row["renewals"],
            "year_registered": row["year_registered"],
        }
        batch.append(doc)

        if len(batch) >= BATCH_SIZE:
            patrons_col.insert_many(batch)
            total_inserted += len(batch)
            print(f"Inserted {total_inserted:,} documents...")
            batch.clear()

    if batch:
        patrons_col.insert_many(batch)
        total_inserted += len(batch)

    print("Creating unique index on patron_id...")
    patrons_col.create_index([("patron_id", ASCENDING)], unique=True)

    cursor.close()
    mysql_conn.close()
    mongo_client.close()
    print(f"Done, migrated {total_inserted:,} patron documents into '{MONGO_DB_NAME}.patrons'.")


if __name__ == "__main__":
    migrate()

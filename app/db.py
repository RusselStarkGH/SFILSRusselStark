import os
import mysql.connector

db_config = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", 3307)),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "assignment1"),
}

def get_connection():
    return mysql.connector.connect(**db_config)

def fetch_patrons(limit=50, offset=0, search_id=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    base_sql = """
    SELECT
        s.patron_id,
        pt.patron_type_definition AS patron_type,
        l.library_definition AS home_library,
        n.notification_definition AS notification,
        s.`Age Range` as age_range,
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
    """

    if search_id is not None:
        cursor.execute(base_sql + " WHERE s.patron_id = %s", (search_id,))
    else:
        cursor.execute(base_sql + " ORDER BY s.patron_id ASC LIMIT %s OFFSET %s", (limit, offset))

    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def fetch_lookup_options():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT patron_type_code, patron_type_definition FROM patron_type ORDER BY patron_type_code")
    patron_types = cursor.fetchall()

    cursor.execute("SELECT library_code, library_definition FROM library ORDER BY library_definition")
    library = cursor.fetchall()

    cursor.execute("SELECT notification_code, notification_definition FROM notification ORDER BY notification_definition")
    notification = cursor.fetchall()

    cursor.close()
    conn.close()
    return patron_types, library, notification

def insert_patron(pt_code, lib_code, notif_code, age_range, checkouts, renewals, year_reg):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
        INSERT INTO sfpldata (
            `Patron Type Code\npatron_type_code`,
            `Home Library Code\nhome_library_code`,
            `Notification Preference Code\nnotification_medium_code`,
            `Age Range`,
            `Total Checkouts\ncheckout_total`,
            `Total Renewals\nrenewal_total`,
            `Year Patron Registered`
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(sql, (pt_code, lib_code, notif_code, age_range, checkouts, renewals, year_reg))
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return new_id


def update_patron(patron_id, pt_code, lib_code, notif_code, age_range, checkouts, renewals, year_reg):
    conn = get_connection()
    cursor = conn.cursor()
    sql = """
        UPDATE sfpldata
        SET `Patron Type Code\npatron_type_code` = %s,
            `Home Library Code\nhome_library_code` = %s,
            `Notification Preference Code\nnotification_medium_code` = %s,
            `Age Range` = %s,
            `Total Checkouts\ncheckout_total` = %s,
            `Total Renewals\nrenewal_total` = %s,
            `Year Patron Registered` = %s
        WHERE patron_id = %s
    """
    cursor.execute(sql, (pt_code, lib_code, notif_code, age_range, checkouts, renewals, year_reg, patron_id))
    conn.commit()
    cursor.close()
    conn.close()


def delete_patron(patron_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sfpldata WHERE patron_id = %s", (patron_id,))
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    pts, libs, notifs = fetch_lookup_options()
    print(f"Loaded {len(pts)} patron types, {len(libs)} library, {len(notifs)} notification types.")

    sample = fetch_patrons(limit=3)
    for row in sample:
        print(row)
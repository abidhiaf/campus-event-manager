"""
Initializes the campus_events database: creates the two mandatory collections
with MongoDB schema validation, then builds the required indexes.

Run with:  python database/init.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from db import get_client, DB_NAME  # noqa: E402

USERS_VALIDATOR = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "user validation",
        "required": ["firstName", "lastName", "email", "department", "role", "interests", "createdAt"],
        "properties": {
            "firstName": {"bsonType": "string", "minLength": 1},
            "lastName": {"bsonType": "string", "minLength": 1},
            "email": {
                "bsonType": "string",
                "pattern": r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
                "description": "must be a valid email address",
            },
            "department": {"bsonType": "string", "minLength": 1},
            "role": {"bsonType": "string", "minLength": 1},
            "interests": {"bsonType": "array", "items": {"bsonType": "string"}},
            "createdAt": {"bsonType": "date"},
        },
    }
}

EVENTS_VALIDATOR = {
    "$and": [
        {
            "$jsonSchema": {
                "bsonType": "object",
                "title": "event validation",
                "required": [
                    "title", "description", "category", "tags", "startDate", "endDate",
                    "capacity", "location", "organizerId", "registrations", "createdAt",
                ],
                "properties": {
                    "title": {"bsonType": "string", "minLength": 1},
                    "description": {"bsonType": "string"},
                    "category": {"bsonType": "string", "minLength": 1},
                    "tags": {"bsonType": "array", "items": {"bsonType": "string"}},
                    "startDate": {"bsonType": "date"},
                    "endDate": {"bsonType": "date"},
                    "capacity": {"bsonType": "int", "minimum": 1},
                    "location": {
                        "bsonType": "object",
                        "required": ["building", "room", "campus"],
                        "properties": {
                            "building": {"bsonType": "string"},
                            "room": {"bsonType": "string"},
                            "campus": {"bsonType": "string"},
                        },
                    },
                    "organizerId": {"bsonType": "objectId"},
                    "registrations": {
                        "bsonType": "array",
                        "items": {
                            "bsonType": "object",
                            "required": ["userId", "registeredAt", "status"],
                            "properties": {
                                "userId": {"bsonType": "objectId"},
                                "registeredAt": {"bsonType": "date"},
                                "status": {"enum": ["confirmed", "cancelled", "waiting"]},
                            },
                        },
                    },
                    "createdAt": {"bsonType": "date"},
                },
            }
        },
        {"$expr": {"$gte": ["$endDate", "$startDate"]}},
    ]
}


def ensure_collection(db, name, validator):
    if name in db.list_collection_names():
        db.command("collMod", name, validator=validator, validationLevel="strict")
    else:
        db.create_collection(name, validator=validator, validationLevel="strict")


def main():
    client = get_client()
    db = client[DB_NAME]

    ensure_collection(db, "users", USERS_VALIDATOR)
    ensure_collection(db, "events", EVENTS_VALIDATOR)

    db.users.create_index("email", unique=True, name="uniq_email")
    db.events.create_index("startDate", name="idx_startDate")
    db.events.create_index("category", name="idx_category")
    db.events.create_index("tags", name="idx_tags")
    db.events.create_index("organizerId", name="idx_organizerId")

    print(f"Database '{DB_NAME}' initialized.")
    print("users indexes:  ", list(db.users.index_information().keys()))
    print("events indexes: ", list(db.events.index_information().keys()))

    client.close()


if __name__ == "__main__":
    main()

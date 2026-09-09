from flask import Blueprint, render_template

from db import get_db

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")


def registrations_by_category(db):
    """Analysis A: events + confirmed registrations, grouped by category."""
    pipeline = [
        {"$unwind": {"path": "$registrations", "preserveNullAndEmptyArrays": True}},
        {
            "$group": {
                "_id": "$category",
                "eventIds": {"$addToSet": "$_id"},
                "confirmedRegistrations": {
                    "$sum": {"$cond": [{"$eq": ["$registrations.status", "confirmed"]}, 1, 0]}
                },
            }
        },
        {
            "$project": {
                "_id": 0,
                "category": "$_id",
                "eventCount": {"$size": "$eventIds"},
                "confirmedRegistrations": 1,
            }
        },
        {"$sort": {"confirmedRegistrations": -1}},
    ]
    return list(db.events.aggregate(pipeline))


def top_popular_events(db, limit=5):
    """Analysis B: top N events by confirmed registrations, with occupancy %."""
    pipeline = [
        {
            "$addFields": {
                "confirmedCount": {
                    "$size": {
                        "$filter": {
                            "input": "$registrations",
                            "as": "r",
                            "cond": {"$eq": ["$$r.status", "confirmed"]},
                        }
                    }
                }
            }
        },
        {
            "$addFields": {
                "occupancyPct": {
                    "$round": [{"$multiply": [{"$divide": ["$confirmedCount", "$capacity"]}, 100]}, 1]
                }
            }
        },
        {"$sort": {"confirmedCount": -1}},
        {"$limit": limit},
        {"$project": {"title": 1, "category": 1, "capacity": 1, "confirmedCount": 1, "occupancyPct": 1}},
    ]
    return list(db.events.aggregate(pipeline))


def users_without_registration(db):
    """Analysis C: users who never registered for any event, via $lookup + filter."""
    pipeline = [
        {
            "$lookup": {
                "from": "events",
                "let": {"uid": "$_id"},
                "pipeline": [
                    {"$unwind": "$registrations"},
                    {"$match": {"$expr": {"$eq": ["$registrations.userId", "$$uid"]}}},
                ],
                "as": "regs",
            }
        },
        {"$match": {"regs": {"$size": 0}}},
        {"$project": {"firstName": 1, "lastName": 1, "email": 1, "department": 1, "role": 1}},
        {"$sort": {"lastName": 1}},
    ]
    return list(db.users.aggregate(pipeline))


def events_above_average_occupancy(db):
    """Analysis D: events whose occupancy % is above the overall average, via $facet + $avg."""
    pipeline = [
        {
            "$addFields": {
                "confirmedCount": {
                    "$size": {
                        "$filter": {
                            "input": "$registrations",
                            "as": "r",
                            "cond": {"$eq": ["$$r.status", "confirmed"]},
                        }
                    }
                }
            }
        },
        {
            "$addFields": {
                "occupancyPct": {
                    "$round": [{"$multiply": [{"$divide": ["$confirmedCount", "$capacity"]}, 100]}, 1]
                }
            }
        },
        {
            "$facet": {
                "events": [
                    {"$project": {"title": 1, "category": 1, "capacity": 1, "confirmedCount": 1, "occupancyPct": 1}}
                ],
                "stats": [{"$group": {"_id": None, "avgOccupancy": {"$avg": "$occupancyPct"}}}],
            }
        },
        {"$unwind": "$stats"},
        {
            "$project": {
                "avgOccupancy": {"$round": ["$stats.avgOccupancy", 1]},
                "events": {
                    "$filter": {
                        "input": "$events",
                        "as": "e",
                        "cond": {"$gt": ["$$e.occupancyPct", "$stats.avgOccupancy"]},
                    }
                },
            }
        },
    ]
    result = list(db.events.aggregate(pipeline))
    if not result:
        return 0, []
    doc = result[0]
    events = sorted(doc["events"], key=lambda e: e["occupancyPct"], reverse=True)
    return doc["avgOccupancy"], events


def most_used_tags(db):
    """Analysis E: number of events using each tag, most frequent first."""
    pipeline = [
        {"$unwind": "$tags"},
        {"$group": {"_id": "$tags", "eventCount": {"$sum": 1}}},
        {"$sort": {"eventCount": -1}},
    ]
    return list(db.events.aggregate(pipeline))


def events_by_month(db):
    """Analysis F: number of events and registrations grouped by month."""
    pipeline = [
        {
            "$addFields": {
                "month": {"$dateToString": {"format": "%Y-%m", "date": "$startDate"}},
                "regCount": {"$size": "$registrations"},
            }
        },
        {
            "$group": {
                "_id": "$month",
                "eventCount": {"$sum": 1},
                "totalRegistrations": {"$sum": "$regCount"},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    return list(db.events.aggregate(pipeline))


@analytics_bp.route("/")
def index():
    db = get_db()

    avg_occupancy, above_avg_events = events_above_average_occupancy(db)

    return render_template(
        "analytics.html",
        by_category=registrations_by_category(db),
        top_events=top_popular_events(db),
        no_registration_users=users_without_registration(db),
        avg_occupancy=avg_occupancy,
        above_avg_events=above_avg_events,
        used_tags=most_used_tags(db),
        by_month=events_by_month(db),
    )

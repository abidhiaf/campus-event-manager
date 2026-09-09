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


def build_insights(by_category, no_registration_users, avg_occupancy, above_avg_events, used_tags, by_month):
    """Turns the raw aggregation results above into a handful of plain-English
    takeaways. Every number here comes straight from the pipelines already
    computed for this page - nothing is hard-coded."""
    insights = []

    if by_category:
        total_confirmed = sum(row["confirmedRegistrations"] for row in by_category)
        top = by_category[0]
        if total_confirmed > 0:
            share = round(top["confirmedRegistrations"] / total_confirmed * 100, 1)
            insights.append(
                f"“{top['category']}” leads engagement: {top['confirmedRegistrations']} confirmed "
                f"registrations across {top['eventCount']} events — {share}% of all confirmed sign-ups."
            )

    if used_tags:
        top_tag = used_tags[0]
        insights.append(
            f"“{top_tag['_id']}” is the most common tag, used on {top_tag['eventCount']} events."
        )

    if by_month:
        busiest = max(by_month, key=lambda m: m["totalRegistrations"])
        insights.append(
            f"{busiest['_id']} is the busiest month: {busiest['eventCount']} events and "
            f"{busiest['totalRegistrations']} registrations."
        )

    if above_avg_events:
        insights.append(
            f"{len(above_avg_events)} event(s) run above the {avg_occupancy}% average occupancy rate, "
            f"led by “{above_avg_events[0]['title']}” at {above_avg_events[0]['occupancyPct']}%."
        )

    if no_registration_users:
        insights.append(
            f"{len(no_registration_users)} user(s) have not registered for a single event yet "
            "— worth a reminder email."
        )

    return insights


@analytics_bp.route("/")
def index():
    db = get_db()

    by_category = registrations_by_category(db)
    no_registration_users = users_without_registration(db)
    avg_occupancy, above_avg_events = events_above_average_occupancy(db)
    used_tags = most_used_tags(db)
    by_month = events_by_month(db)

    insights = build_insights(
        by_category, no_registration_users, avg_occupancy, above_avg_events, used_tags, by_month
    )

    return render_template(
        "analytics.html",
        by_category=by_category,
        top_events=top_popular_events(db),
        no_registration_users=no_registration_users,
        avg_occupancy=avg_occupancy,
        above_avg_events=above_avg_events,
        used_tags=used_tags,
        by_month=by_month,
        insights=insights,
    )

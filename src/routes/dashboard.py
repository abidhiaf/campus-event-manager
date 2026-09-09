from datetime import datetime

from flask import Blueprint, render_template

from db import get_db

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    db = get_db()
    now = datetime.utcnow()

    users_count = db.users.count_documents({})
    events_count = db.events.count_documents({})
    upcoming_count = db.events.count_documents({"startDate": {"$gt": now}})

    # Array processing: total registrations across all events, via $unwind + $count.
    total_regs_pipeline = [
        {"$unwind": "$registrations"},
        {"$count": "total"},
    ]
    total_regs_result = list(db.events.aggregate(total_regs_pipeline))
    total_registrations = total_regs_result[0]["total"] if total_regs_result else 0

    next_events = list(
        db.events.find({"startDate": {"$gt": now}})
        .sort("startDate", 1)
        .limit(5)
    )

    # Most popular event based on confirmed registrations, via $size on a filtered array.
    popular_pipeline = [
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
        {"$sort": {"confirmedCount": -1}},
        {"$limit": 1},
    ]
    popular_result = list(db.events.aggregate(popular_pipeline))
    most_popular_event = popular_result[0] if popular_result else None

    return render_template(
        "dashboard.html",
        users_count=users_count,
        events_count=events_count,
        upcoming_count=upcoming_count,
        total_registrations=total_registrations,
        next_events=next_events,
        most_popular_event=most_popular_event,
        now=now,
    )

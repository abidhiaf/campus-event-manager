from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, flash, redirect, render_template, request, url_for

from db import get_db

events_bp = Blueprint("events", __name__, url_prefix="/events")


def confirmed_count(event):
    return len([r for r in event.get("registrations", []) if r["status"] == "confirmed"])


def to_object_id(raw_id):
    try:
        return ObjectId(raw_id)
    except (InvalidId, TypeError):
        return None


@events_bp.route("/")
def list_events():
    db = get_db()
    now = datetime.utcnow()

    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    tag = request.args.get("tag", "").strip()
    time_filter = request.args.get("time", "").strip()  # "upcoming" | "past"
    sort_dir = request.args.get("sort", "asc")

    query = {}
    conditions = []
    if search:
        conditions.append({"title": {"$regex": search, "$options": "i"}})
    if category:
        conditions.append({"category": category})
    if tag:
        conditions.append({"tags": tag})
    if time_filter == "upcoming":
        conditions.append({"startDate": {"$gt": now}})
    elif time_filter == "past":
        conditions.append({"startDate": {"$lte": now}})

    if conditions:
        query["$and"] = conditions

    sort_order = 1 if sort_dir == "asc" else -1
    events = list(db.events.find(query).sort("startDate", sort_order))

    for e in events:
        e["confirmedCount"] = confirmed_count(e)
        e["isFull"] = e["confirmedCount"] >= e["capacity"]

    categories = [c for c in db.events.distinct("category") if c]
    tags = [t for t in db.events.distinct("tags") if t]

    return render_template(
        "events_list.html",
        events=events,
        categories=sorted(categories),
        tags=sorted(tags),
        search=search,
        category=category,
        tag=tag,
        time_filter=time_filter,
        sort_dir=sort_dir,
        now=now,
    )


@events_bp.route("/new", methods=["GET", "POST"])
def new_event():
    db = get_db()

    if request.method == "POST":
        errors = validate_event_form(request.form)
        if errors:
            for err in errors:
                flash(err, "error")
            users = list(db.users.find().sort([("lastName", 1), ("firstName", 1)]))
            return render_template("event_form.html", event=request.form, mode="create", users=users)

        organizer_id = to_object_id(request.form.get("organizerId"))
        doc = {
            "title": request.form["title"].strip(),
            "description": request.form.get("description", "").strip(),
            "category": request.form["category"].strip(),
            "tags": parse_tags(request.form.get("tags", "")),
            "startDate": parse_datetime(request.form["startDate"]),
            "endDate": parse_datetime(request.form["endDate"]),
            "capacity": int(request.form["capacity"]),
            "location": {
                "building": request.form.get("building", "").strip(),
                "room": request.form.get("room", "").strip(),
                "campus": request.form.get("campus", "").strip(),
            },
            "organizerId": organizer_id,
            "registrations": [],
            "createdAt": datetime.utcnow(),
        }
        db.events.insert_one(doc)
        flash("Event created successfully.", "success")
        return redirect(url_for("events.list_events"))

    users = list(db.users.find().sort([("lastName", 1), ("firstName", 1)]))
    return render_template("event_form.html", event=None, mode="create", users=users)


@events_bp.route("/<event_id>/edit", methods=["GET", "POST"])
def edit_event(event_id):
    db = get_db()
    oid = to_object_id(event_id)
    if oid is None:
        flash("Invalid event identifier.", "error")
        return redirect(url_for("events.list_events"))

    event = db.events.find_one({"_id": oid})
    if event is None:
        flash("Event not found.", "error")
        return redirect(url_for("events.list_events"))

    if request.method == "POST":
        errors = validate_event_form(request.form)
        if errors:
            for err in errors:
                flash(err, "error")
            users = list(db.users.find().sort([("lastName", 1), ("firstName", 1)]))
            return render_template("event_form.html", event=request.form, mode="edit", event_id=event_id, users=users)

        db.events.update_one(
            {"_id": oid},
            {
                "$set": {
                    "title": request.form["title"].strip(),
                    "description": request.form.get("description", "").strip(),
                    "category": request.form["category"].strip(),
                    "tags": parse_tags(request.form.get("tags", "")),
                    "startDate": parse_datetime(request.form["startDate"]),
                    "endDate": parse_datetime(request.form["endDate"]),
                    "capacity": int(request.form["capacity"]),
                    "location": {
                        "building": request.form.get("building", "").strip(),
                        "room": request.form.get("room", "").strip(),
                        "campus": request.form.get("campus", "").strip(),
                    },
                    "organizerId": to_object_id(request.form.get("organizerId")),
                }
            },
        )
        flash("Event updated successfully.", "success")
        return redirect(url_for("events.event_detail", event_id=event_id))

    form_data = {
        "title": event["title"],
        "description": event["description"],
        "category": event["category"],
        "tags": ", ".join(event.get("tags", [])),
        "startDate": event["startDate"].strftime("%Y-%m-%dT%H:%M"),
        "endDate": event["endDate"].strftime("%Y-%m-%dT%H:%M"),
        "capacity": event["capacity"],
        "building": event["location"]["building"],
        "room": event["location"]["room"],
        "campus": event["location"]["campus"],
        "organizerId": str(event["organizerId"]),
    }
    users = list(db.users.find().sort([("lastName", 1), ("firstName", 1)]))
    return render_template("event_form.html", event=form_data, mode="edit", event_id=event_id, users=users)


@events_bp.route("/<event_id>/delete", methods=["POST"])
def delete_event(event_id):
    db = get_db()
    oid = to_object_id(event_id)
    if oid is None:
        flash("Invalid event identifier.", "error")
        return redirect(url_for("events.list_events"))

    result = db.events.delete_one({"_id": oid})
    if result.deleted_count:
        flash("Event deleted.", "success")
    else:
        flash("Event not found.", "error")
    return redirect(url_for("events.list_events"))


@events_bp.route("/<event_id>")
def event_detail(event_id):
    db = get_db()
    oid = to_object_id(event_id)
    if oid is None:
        flash("Invalid event identifier.", "error")
        return redirect(url_for("events.list_events"))

    event = db.events.find_one({"_id": oid})
    if event is None:
        flash("Event not found.", "error")
        return redirect(url_for("events.list_events"))

    organizer = db.users.find_one({"_id": event["organizerId"]})

    participant_ids = [r["userId"] for r in event["registrations"]]
    participants_by_id = {
        u["_id"]: u for u in db.users.find({"_id": {"$in": participant_ids}})
    }
    participants = []
    for r in event["registrations"]:
        user = participants_by_id.get(r["userId"])
        participants.append({
            "user": user,
            "status": r["status"],
            "registeredAt": r["registeredAt"],
        })

    c_count = confirmed_count(event)
    occupancy = round((c_count / event["capacity"]) * 100, 1) if event["capacity"] else 0

    all_users = list(db.users.find().sort([("lastName", 1), ("firstName", 1)]))
    registered_user_ids = {str(uid) for uid in participant_ids}

    return render_template(
        "event_detail.html",
        event=event,
        organizer=organizer,
        participants=participants,
        confirmed_count=c_count,
        occupancy=occupancy,
        is_full=c_count >= event["capacity"],
        all_users=all_users,
        registered_user_ids=registered_user_ids,
        now=datetime.utcnow(),
    )


@events_bp.route("/<event_id>/register", methods=["POST"])
def register_user(event_id):
    db = get_db()
    oid = to_object_id(event_id)
    user_oid = to_object_id(request.form.get("userId"))

    if oid is None or user_oid is None:
        flash("Invalid identifier.", "error")
        return redirect(url_for("events.list_events"))

    event = db.events.find_one({"_id": oid})
    if event is None:
        flash("Event not found.", "error")
        return redirect(url_for("events.list_events"))

    if db.users.find_one({"_id": user_oid}) is None:
        flash("User not found.", "error")
        return redirect(url_for("events.event_detail", event_id=event_id))

    already_registered = any(str(r["userId"]) == str(user_oid) for r in event["registrations"])
    if already_registered:
        flash("This user is already registered for this event.", "error")
        return redirect(url_for("events.event_detail", event_id=event_id))

    c_count = confirmed_count(event)
    status = "confirmed" if c_count < event["capacity"] else "waiting"
    if status == "waiting":
        flash("The event is full: the user has been placed on the waiting list.", "success")
    else:
        flash("User registered successfully.", "success")

    db.events.update_one(
        {"_id": oid},
        {
            "$addToSet": {
                "registrations": {
                    "userId": user_oid,
                    "registeredAt": datetime.utcnow(),
                    "status": status,
                }
            }
        },
    )
    return redirect(url_for("events.event_detail", event_id=event_id))


@events_bp.route("/<event_id>/unregister", methods=["POST"])
def unregister_user(event_id):
    db = get_db()
    oid = to_object_id(event_id)
    user_oid = to_object_id(request.form.get("userId"))

    if oid is None or user_oid is None:
        flash("Invalid identifier.", "error")
        return redirect(url_for("events.list_events"))

    db.events.update_one(
        {"_id": oid},
        {"$pull": {"registrations": {"userId": user_oid}}},
    )
    flash("Registration removed.", "success")
    return redirect(url_for("events.event_detail", event_id=event_id))


def parse_tags(raw):
    return [t.strip() for t in raw.split(",") if t.strip()]


def parse_datetime(raw):
    return datetime.strptime(raw, "%Y-%m-%dT%H:%M")


def validate_event_form(form):
    errors = []
    if not form.get("title", "").strip():
        errors.append("Event title cannot be empty.")

    try:
        capacity = int(form.get("capacity", "0"))
        if capacity <= 0:
            errors.append("Capacity must be greater than 0.")
    except ValueError:
        errors.append("Capacity must be a number.")

    try:
        start = parse_datetime(form["startDate"])
        end = parse_datetime(form["endDate"])
        if end < start:
            errors.append("The end date cannot be before the start date.")
    except (KeyError, ValueError):
        errors.append("Start date and end date are required and must be valid.")

    if not form.get("organizerId"):
        errors.append("An organizer must be selected.")

    return errors

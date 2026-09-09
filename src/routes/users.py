from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, flash, redirect, render_template, request, url_for
from pymongo.errors import DuplicateKeyError

from db import get_db

users_bp = Blueprint("users", __name__, url_prefix="/users")


def to_object_id(raw_id):
    try:
        return ObjectId(raw_id)
    except (InvalidId, TypeError):
        return None


def registration_counts(db):
    """Number of registrations per user, across all events, via $unwind + $group."""
    pipeline = [
        {"$unwind": "$registrations"},
        {"$group": {"_id": "$registrations.userId", "count": {"$sum": 1}}},
    ]
    return {str(row["_id"]): row["count"] for row in db.events.aggregate(pipeline)}


@users_bp.route("/")
def list_users():
    db = get_db()

    search = request.args.get("q", "").strip()
    department = request.args.get("department", "").strip()
    role = request.args.get("role", "").strip()

    conditions = []
    if search:
        conditions.append({
            "$or": [
                {"firstName": {"$regex": search, "$options": "i"}},
                {"lastName": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
            ]
        })
    if department:
        conditions.append({"department": department})
    if role:
        conditions.append({"role": role})

    query = {"$and": conditions} if conditions else {}
    users = list(db.users.find(query).sort([("lastName", 1), ("firstName", 1)]))

    counts = registration_counts(db)
    for u in users:
        u["registrationCount"] = counts.get(str(u["_id"]), 0)

    departments = sorted(d for d in db.users.distinct("department") if d)
    roles = sorted(r for r in db.users.distinct("role") if r)

    return render_template(
        "users_list.html",
        users=users,
        departments=departments,
        roles=roles,
        search=search,
        department=department,
        role=role,
    )


@users_bp.route("/new", methods=["GET", "POST"])
def new_user():
    db = get_db()

    if request.method == "POST":
        errors = validate_user_form(request.form)
        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("user_form.html", user=request.form, mode="create")

        doc = {
            "firstName": request.form["firstName"].strip(),
            "lastName": request.form["lastName"].strip(),
            "email": request.form["email"].strip().lower(),
            "department": request.form["department"].strip(),
            "role": request.form["role"].strip(),
            "interests": parse_interests(request.form.get("interests", "")),
            "createdAt": datetime.utcnow(),
        }
        try:
            db.users.insert_one(doc)
        except DuplicateKeyError:
            flash("A user with this email already exists.", "error")
            return render_template("user_form.html", user=request.form, mode="create")

        flash("User created successfully.", "success")
        return redirect(url_for("users.list_users"))

    return render_template("user_form.html", user=None, mode="create")


@users_bp.route("/<user_id>/edit", methods=["GET", "POST"])
def edit_user(user_id):
    db = get_db()
    oid = to_object_id(user_id)
    if oid is None:
        flash("Invalid user identifier.", "error")
        return redirect(url_for("users.list_users"))

    user = db.users.find_one({"_id": oid})
    if user is None:
        flash("User not found.", "error")
        return redirect(url_for("users.list_users"))

    if request.method == "POST":
        errors = validate_user_form(request.form)
        if errors:
            for err in errors:
                flash(err, "error")
            return render_template("user_form.html", user=request.form, mode="edit", user_id=user_id)

        try:
            db.users.update_one(
                {"_id": oid},
                {
                    "$set": {
                        "firstName": request.form["firstName"].strip(),
                        "lastName": request.form["lastName"].strip(),
                        "email": request.form["email"].strip().lower(),
                        "department": request.form["department"].strip(),
                        "role": request.form["role"].strip(),
                        "interests": parse_interests(request.form.get("interests", "")),
                    }
                },
            )
        except DuplicateKeyError:
            flash("A user with this email already exists.", "error")
            return render_template("user_form.html", user=request.form, mode="edit", user_id=user_id)

        flash("User updated successfully.", "success")
        return redirect(url_for("users.user_detail", user_id=user_id))

    form_data = {
        "firstName": user["firstName"],
        "lastName": user["lastName"],
        "email": user["email"],
        "department": user["department"],
        "role": user["role"],
        "interests": ", ".join(user.get("interests", [])),
    }
    return render_template("user_form.html", user=form_data, mode="edit", user_id=user_id)


@users_bp.route("/<user_id>/delete", methods=["POST"])
def delete_user(user_id):
    db = get_db()
    oid = to_object_id(user_id)
    if oid is None:
        flash("Invalid user identifier.", "error")
        return redirect(url_for("users.list_users"))

    is_organizer = db.events.count_documents({"organizerId": oid}) > 0
    is_registered = db.events.count_documents({"registrations.userId": oid}) > 0

    if is_organizer or is_registered:
        flash(
            "This user cannot be deleted: they are still referenced as an organizer "
            "or in event registrations. Remove those references first.",
            "error",
        )
        return redirect(url_for("users.user_detail", user_id=user_id))

    result = db.users.delete_one({"_id": oid})
    if result.deleted_count:
        flash("User deleted.", "success")
    else:
        flash("User not found.", "error")
    return redirect(url_for("users.list_users"))


@users_bp.route("/<user_id>")
def user_detail(user_id):
    db = get_db()
    oid = to_object_id(user_id)
    if oid is None:
        flash("Invalid user identifier.", "error")
        return redirect(url_for("users.list_users"))

    user = db.users.find_one({"_id": oid})
    if user is None:
        flash("User not found.", "error")
        return redirect(url_for("users.list_users"))

    # Combine users and events with $lookup + a sub-pipeline that unwinds registrations.
    pipeline = [
        {"$match": {"_id": oid}},
        {
            "$lookup": {
                "from": "events",
                "let": {"uid": "$_id"},
                "pipeline": [
                    {"$unwind": "$registrations"},
                    {"$match": {"$expr": {"$eq": ["$registrations.userId", "$$uid"]}}},
                    {
                        "$project": {
                            "_id": 1,
                            "title": 1,
                            "category": 1,
                            "startDate": 1,
                            "status": "$registrations.status",
                        }
                    },
                    {"$sort": {"startDate": 1}},
                ],
                "as": "registeredEvents",
            }
        },
    ]
    result = list(db.users.aggregate(pipeline))
    registered_events = result[0]["registeredEvents"] if result else []

    now = datetime.utcnow()
    upcoming = [e for e in registered_events if e["startDate"] > now]
    past = [e for e in registered_events if e["startDate"] <= now]

    return render_template(
        "user_detail.html",
        user=user,
        registered_events=registered_events,
        upcoming_count=len(upcoming),
        past_count=len(past),
        now=now,
    )


def parse_interests(raw):
    return [t.strip() for t in raw.split(",") if t.strip()]


def validate_user_form(form):
    import re

    errors = []
    if not form.get("firstName", "").strip():
        errors.append("First name cannot be empty.")
    if not form.get("lastName", "").strip():
        errors.append("Last name cannot be empty.")

    email = form.get("email", "").strip()
    if not email or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        errors.append("A valid email address is required.")

    if not form.get("department", "").strip():
        errors.append("Department cannot be empty.")
    if not form.get("role", "").strip():
        errors.append("Role cannot be empty.")

    return errors

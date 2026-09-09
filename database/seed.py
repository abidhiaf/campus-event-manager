"""
Populates campus_events with a reproducible dataset:
15 users, 18 events (5 categories, 10 tags), 40+ registrations.

Run with:  python database/seed.py
This script always clears the two collections first, so it can be re-run safely.
"""
import os
import random
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from db import get_client, DB_NAME  # noqa: E402

random.seed(42)

TODAY = datetime(2026, 9, 9, 9, 0, 0)

USERS = [
    {"firstName": "Alice", "lastName": "Martin", "email": "alice.martin@campus.fr",
     "department": "Data Engineering", "role": "student",
     "interests": ["artificial intelligence", "cloud computing", "data science"]},
    {"firstName": "Yanis", "lastName": "Benali", "email": "yanis.benali@campus.fr",
     "department": "Computer Science", "role": "student",
     "interests": ["cybersecurity", "open source"]},
    {"firstName": "Chloe", "lastName": "Dubois", "email": "chloe.dubois@campus.fr",
     "department": "Design", "role": "student",
     "interests": ["design", "photography"]},
    {"firstName": "Marco", "lastName": "Rinaldi", "email": "marco.rinaldi@campus.fr",
     "department": "Business Administration", "role": "student",
     "interests": ["entrepreneurship", "networking"]},
    {"firstName": "Fatou", "lastName": "Diallo", "email": "fatou.diallo@campus.fr",
     "department": "Data Engineering", "role": "student",
     "interests": ["data science", "artificial intelligence", "sports"]},
    {"firstName": "Lucas", "lastName": "Bernard", "email": "lucas.bernard@campus.fr",
     "department": "Mechanical Engineering", "role": "student",
     "interests": ["robotics", "sports"]},
    {"firstName": "Sofia", "lastName": "Costa", "email": "sofia.costa@campus.fr",
     "department": "Computer Science", "role": "student",
     "interests": ["open source", "cloud computing", "volunteering"]},
    {"firstName": "Hugo", "lastName": "Lefevre", "email": "hugo.lefevre@campus.fr",
     "department": "Physics", "role": "student",
     "interests": ["robotics", "music"]},
    {"firstName": "Nora", "lastName": "El Amrani", "email": "nora.elamrani@campus.fr",
     "department": "Business Administration", "role": "student",
     "interests": ["entrepreneurship", "design"]},
    {"firstName": "Tom", "lastName": "Girard", "email": "tom.girard@campus.fr",
     "department": "Computer Science", "role": "student",
     "interests": ["cybersecurity", "artificial intelligence"]},
    {"firstName": "Lea", "lastName": "Moreau", "email": "lea.moreau@campus.fr",
     "department": "Data Engineering", "role": "student",
     "interests": ["data science", "volunteering", "music"]},
    {"firstName": "Ibrahim", "lastName": "Toure", "email": "ibrahim.toure@campus.fr",
     "department": "Mechanical Engineering", "role": "student",
     "interests": ["robotics", "entrepreneurship"]},
    {"firstName": "Claire", "lastName": "Petit", "email": "claire.petit@campus.fr",
     "department": "Computer Science", "role": "staff",
     "interests": ["open source", "networking", "cloud computing"]},
    {"firstName": "David", "lastName": "Nguyen", "email": "david.nguyen@campus.fr",
     "department": "Data Engineering", "role": "professor",
     "interests": ["data science", "artificial intelligence"]},
    {"firstName": "Emma", "lastName": "Rousseau", "email": "emma.rousseau@campus.fr",
     "department": "Design", "role": "staff",
     "interests": ["design", "photography", "volunteering"]},
]

TAGS_POOL = [
    "python", "ai", "networking", "career", "design",
    "cloud", "opensource", "robotics", "startup", "security",
]

# (title, category, description, tag subset, month offset from Sept 2026, day, duration_hours, capacity, building, room, organizer_index)
EVENT_DEFS = [
    ("Intro to Python for Data Science", "Workshop",
     "Hands-on workshop covering pandas, numpy and a first predictive model.",
     ["python", "ai"], -1, 15, 3, 25, "Innovation Center", "B204", 13),
    ("Cloud Architecture Fundamentals", "Talk",
     "An overview of cloud-native architectures with real production examples.",
     ["cloud", "career"], -1, 22, 2, 40, "Innovation Center", "A101", 12),
    ("Campus Hackathon: Smart Mobility", "Hackathon",
     "48-hour hackathon building mobility solutions for the campus.",
     ["startup", "python", "opensource"], 0, 5, 48, 30, "Tech Hub", "Lab 1", 13),
    ("Cybersecurity Career Night", "Career Fair",
     "Meet security teams from partner companies and learn about open roles.",
     ["security", "career", "networking"], 0, 9, 3, 60, "Main Hall", "Auditorium", 12),
    ("Student Robotics Meetup", "Meetup",
     "Monthly meetup for the robotics club to share ongoing projects.",
     ["robotics", "opensource"], 0, 12, 2, 10, "Engineering Building", "Workshop 3", 14),
    ("Design Thinking Sprint", "Workshop",
     "A one-day sprint applying design thinking to campus life problems.",
     ["design", "startup"], 0, 18, 6, 20, "Creative Studio", "S2", 14),
    ("Intro to Cloud Security", "Talk",
     "Practical talk on securing cloud workloads, with a live Q&A.",
     ["cloud", "security"], 0, 24, 2, 35, "Innovation Center", "A102", 12),
    ("Open Source Contribution Day", "Workshop",
     "Guided session to make your first contribution to an open-source project.",
     ["opensource", "python"], 1, 3, 4, 25, "Tech Hub", "Lab 2", 13),
    ("Entrepreneurship 101", "Talk",
     "Founders share lessons learned building their first startup.",
     ["startup", "career"], 1, 8, 2, 50, "Main Hall", "Auditorium", 12),
    ("AI in Healthcare Panel", "Talk",
     "Panel discussion on applications of AI in modern healthcare.",
     ["ai", "career"], 1, 14, 2, 45, "Innovation Center", "A101", 13),
    ("Networking Night with Alumni", "Meetup",
     "Informal evening to connect current students with campus alumni.",
     ["networking", "career"], 1, 20, 3, 60, "Main Hall", "Terrace", 12),
    ("Robotics Hackathon", "Hackathon",
     "24-hour challenge to build and program an autonomous robot.",
     ["robotics", "python"], 1, 27, 24, 24, "Engineering Building", "Workshop 1", 14),
    ("UX Research Workshop", "Workshop",
     "Learn practical UX research methods through short exercises.",
     ["design", "networking"], 2, 4, 3, 20, "Creative Studio", "S1", 14),
    ("Security CTF Qualifiers", "Hackathon",
     "Capture-the-flag qualifier round open to all cybersecurity enthusiasts.",
     ["security", "opensource"], 2, 10, 5, 30, "Tech Hub", "Lab 1", 12),
    ("Startup Pitch Night", "Meetup",
     "Student teams pitch their projects in front of a jury of mentors.",
     ["startup", "networking"], 2, 16, 3, 40, "Main Hall", "Auditorium", 12),
    ("Python for Automation", "Workshop",
     "Automate repetitive tasks with Python scripts and scheduled jobs.",
     ["python", "cloud"], -2, 20, 3, 22, "Innovation Center", "B204", 13),
    ("Career Fair: Tech & Data", "Career Fair",
     "Annual fair bringing together tech and data recruiters on campus.",
     ["career", "networking", "ai"], -2, 27, 5, 80, "Main Hall", "Auditorium", 12),
    ("Design Systems in Practice", "Talk",
     "How growing product teams build and maintain a design system.",
     ["design", "startup"], 2, 22, 2, 30, "Creative Studio", "S2", 14),
]

STATUS_WEIGHTS = ["confirmed"] * 7 + ["waiting"] * 2 + ["cancelled"] * 1


def month_shift(base: datetime, months: int) -> datetime:
    month = base.month - 1 + months
    year = base.year + month // 12
    month = month % 12 + 1
    return base.replace(year=year, month=month)


def build_users():
    docs = []
    for u in USERS:
        docs.append({**u, "createdAt": TODAY - timedelta(days=random.randint(30, 400))})
    return docs


def build_events(user_ids):
    docs = []
    for (title, category, description, tags, month_offset, day, duration_h,
         capacity, building, room, organizer_idx) in EVENT_DEFS:
        base = month_shift(TODAY.replace(day=1), month_offset)
        start = base.replace(day=day, hour=9, minute=0)
        end = start + timedelta(hours=duration_h)
        docs.append({
            "title": title,
            "description": description,
            "category": category,
            "tags": tags,
            "startDate": start,
            "endDate": end,
            "capacity": capacity,
            "location": {"building": building, "room": room, "campus": "Paris"},
            "organizerId": user_ids[organizer_idx],
            "registrations": [],
            "createdAt": TODAY - timedelta(days=random.randint(10, 120)),
        })
    return docs


def build_registrations(events, user_ids, events_with_no_registrations, excluded_user_indices=frozenset()):
    """Mutates events in place, adding a `registrations` array to each,
    while guaranteeing at least 40 registrations overall and never
    registering the same user twice for the same event. Users in
    `excluded_user_indices` are never registered anywhere, so the
    "users with no registration" analysis has a non-empty result."""
    total = 0
    used_by_event = {idx: set() for idx in range(len(events))}
    eligible_pool = [i for i in range(len(user_ids)) if i not in excluded_user_indices]

    def add_registration(idx, uid_idx, status, days_after=1):
        if uid_idx in used_by_event[idx]:
            return False
        used_by_event[idx].add(uid_idx)
        ev = events[idx]
        ev["registrations"].append({
            "userId": user_ids[uid_idx],
            "registeredAt": ev["createdAt"] + timedelta(days=days_after),
            "status": status,
        })
        return True

    for idx, ev in enumerate(events):
        if idx in events_with_no_registrations:
            continue
        candidates = random.sample(eligible_pool, k=random.randint(2, 8))
        for uid_idx in candidates:
            status = random.choice(STATUS_WEIGHTS)
            if add_registration(idx, uid_idx, status, random.randint(1, 20)):
                total += 1

    # Top up if we fell short of the 40-registration minimum.
    attempts = 0
    while total < 40 and attempts < 1000:
        attempts += 1
        idx = random.randrange(len(events))
        if idx in events_with_no_registrations:
            continue
        uid_idx = random.choice(eligible_pool)
        if add_registration(idx, uid_idx, "confirmed", 1):
            total += 1

    # Make one upcoming event visibly full, to exercise the "full" indicator.
    for idx, ev in enumerate(events):
        if ev["startDate"] > TODAY and ev["capacity"] <= 25:
            confirmed = [r for r in ev["registrations"] if r["status"] == "confirmed"]
            missing = ev["capacity"] - len(confirmed)
            available = [i for i in eligible_pool if i not in used_by_event[idx]]
            random.shuffle(available)
            for uid_idx in available[:missing]:
                if add_registration(idx, uid_idx, "confirmed", 2):
                    total += 1
            break

    return total


def main():
    client = get_client()
    db = client[DB_NAME]

    db.events.delete_many({})
    db.users.delete_many({})

    user_docs = build_users()
    result = db.users.insert_many(user_docs)
    user_ids = result.inserted_ids
    print(f"Inserted {len(user_ids)} users.")

    event_docs = build_events(user_ids)

    # Pick 3 events (spread across past/future) to intentionally have zero registrations.
    events_with_no_registrations = {2, 9, 16}

    # Hugo Lefevre (index 7) is intentionally never registered anywhere, so the
    # "users with no registration" analytics view has a non-empty, meaningful result.
    excluded_user_indices = {7}

    total_regs = build_registrations(
        event_docs, user_ids, events_with_no_registrations, excluded_user_indices
    )

    result = db.events.insert_many(event_docs)
    print(f"Inserted {len(result.inserted_ids)} events.")
    print(f"Inserted {total_regs} registrations across events.")

    categories = sorted({e["category"] for e in event_docs})
    tags_used = sorted({t for e in event_docs for t in e["tags"]})
    print(f"Categories ({len(categories)}): {categories}")
    print(f"Tags used ({len(tags_used)}): {tags_used}")

    client.close()


if __name__ == "__main__":
    main()

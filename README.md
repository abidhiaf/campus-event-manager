# Campus Event Manager

[![Tests](https://github.com/YOUR_GITHUB_USERNAME/campus-event-manager/actions/workflows/tests.yml/badge.svg)](https://github.com/YOUR_GITHUB_USERNAME/campus-event-manager/actions/workflows/tests.yml)

A small web application for managing campus events (workshops, talks, meetups, hackathons)
built for the NoSQL Development Project (MCS DE1). It uses MongoDB as its only data store and
a Flask backend that talks to it directly through PyMongo, so every query and aggregation
pipeline stays visible in the source code.

## 1. Purpose

The university has no application to manage its events. Campus Event Manager lets staff:

- browse and manage a catalog of events (create / edit / delete, search, filters);
- register and cancel student registrations for an event, with capacity and waiting-list logic;
- browse the user directory and each user's participation history;
- consult activity indicators computed live from MongoDB (dashboard + analytics page).

## 2. Technology

- **Database**: MongoDB (collections `users` and `events`, schema validation + indexes).
- **Backend**: Python 3, Flask, PyMongo (no ODM - raw MongoDB operations).
- **Frontend**: server-side Jinja2 templates, Bootstrap 5 (via CDN).

## 3. Project structure

```
campus-event-manager/
├── database/
│   ├── init.py     # creates collections, schema validation, indexes
│   └── seed.py     # inserts the reproducible seed dataset
├── src/
│   ├── app.py          # Flask app factory / entry point
│   ├── db.py            # MongoDB connection helper
│   ├── routes/           # one blueprint per page (dashboard, events, users, analytics)
│   ├── templates/        # Jinja2 templates
│   └── static/           # CSS
├── report/
│   └── report.pdf
├── requirements.txt
└── .env.example
```

## 4. Install dependencies

Requires Python 3.10+ and a MongoDB server (local or remote).

```bash
cd campus-event-manager
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 5. Configure the MongoDB connection

Copy the example environment file and adjust it if needed:

```bash
cp .env.example .env
```

`.env` contains:

```
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=campus_events
PORT=5050
```

If you use a remote / Atlas cluster, replace `MONGO_URI` with your connection string
(never commit real credentials - `.env` is git-ignored).

If you don't have MongoDB installed locally (macOS):

```bash
brew tap mongodb/brew
brew install mongodb-community@7.0
brew services start mongodb/brew/mongodb-community@7.0
```

## 6. Initialize and seed the database

```bash
python database/init.py   # creates collections, validation rules and indexes
python database/seed.py   # inserts 15 users, 18 events, 90+ registrations
```

`seed.py` always clears the two collections first, so it can be re-run safely to reset the
dataset to its initial, reproducible state.

## 7. Run the application

```bash
python src/app.py
```

The app runs on **http://localhost:5050** by default (configurable via `PORT`).

## 8. Run the tests

A small pytest suite covers the form-validation rules (empty title, capacity <= 0, end date
before start date, invalid email, etc.) used before any write to MongoDB. It needs no database
connection, and it also runs automatically on every push via GitHub Actions
(`.github/workflows/tests.yml`).

```bash
pytest tests/
```

## 9. Main application pages

| Page | URL | Description |
|---|---|---|
| Dashboard | `/` | Live counts (users, events, upcoming events, registrations), next 5 events, most popular event. |
| Events | `/events/` | Event catalog: search, filter by category / tag / upcoming-past, sort by date, create / edit / delete, "full" indicator. |
| Event detail | `/events/<id>` | Full event info, participant list, register / cancel a user for the event. |
| Users | `/users/` | User directory: search, filter by department / role, create / edit / delete, registration count. |
| User detail | `/users/<id>` | User info, interests, full participation history (via `$lookup`), upcoming/past counts. |
| Analytics | `/analytics/` | Six aggregation-pipeline analyses: registrations by category, top 5 events, users with no registration, events above average occupancy, most used tags, events by month. |

## 10. Author

Ahmed ABIDHIAF

from flask import Flask

from routes.dashboard import dashboard_bp
from routes.events import events_bp
from routes.users import users_bp
from routes.analytics import analytics_bp


def create_app():
    app = Flask(__name__)
    app.secret_key = "campus-event-manager-dev-secret"

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(analytics_bp)

    return app


app = create_app()

if __name__ == "__main__":
    import os
    app.run(debug=True, port=int(os.environ.get("PORT", 5050)))

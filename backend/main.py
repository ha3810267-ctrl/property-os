
import flask
import os

from backend.models.service_provider import ServiceProvider
from backend.models.service_provider_invitation import ServiceProviderInvitation

from dotenv import load_dotenv
from datetime import timedelta

from backend.routes.service_providers import service_providers_bp
from backend.routes.service_provider_invitations import (
    service_provider_invitations_bp
)

from backend.routes.resend_webhooks import (
    resend_webhooks_bp
)

from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from backend.database import db

from backend.models.organisation import Organisation
from backend.models.user import User
from backend.models.property import Property
from backend.models.tenant import Tenant
from backend.models.maintenance_request import MaintenanceRequest
from backend.models.audit_log import AuditLog
from backend.models.external_worker_message import ExternalWorkerMessage

from backend.routes.organisations import organisations_bp
from backend.routes.users import users_bp
from backend.routes.auth import auth_bp
from backend.routes.properties import property_bp
from backend.routes.tenants import tenant_bp
from backend.routes.maintenance import maintenance_bp
from backend.routes.task_assignments import task_assignment_bp
from backend.routes.dashboard import dashboard_bp


load_dotenv()


app = flask.Flask(__name__)


CORS(
    app,
    origins=[
        os.getenv(
            "FRONTEND_URL",
            "http://localhost:5173"
        )
    ],
    supports_credentials=True
)


app.config["JWT_SECRET_KEY"] = os.getenv(
    "JWT_SECRET_KEY"
)

app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
    hours=2
)


jwt = JWTManager(app)


database_url = os.getenv(
    "DATABASE_URL"
)


if (
    database_url
    and database_url.startswith("postgresql://")
):
    database_url = database_url.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1
    )


app.config["SQLALCHEMY_DATABASE_URI"] = database_url


db.init_app(app)


migrate = Migrate(
    app,
    db
)


app.register_blueprint(
    organisations_bp
)

app.register_blueprint(
    property_bp
)

app.register_blueprint(
    users_bp
)

app.register_blueprint(
    auth_bp
)

app.register_blueprint(
    tenant_bp
)

app.register_blueprint(
    maintenance_bp
)

app.register_blueprint(
    task_assignment_bp
)

app.register_blueprint(
    dashboard_bp
)

app.register_blueprint(
    service_providers_bp
)

app.register_blueprint(
    service_provider_invitations_bp
)

app.register_blueprint(
    resend_webhooks_bp
)


@app.route("/")
def home():
    return os.getenv(
        "APP_NAME"
    )


if __name__ == "__main__":
    app.run()

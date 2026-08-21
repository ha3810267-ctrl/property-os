import flask
import os
from dotenv import load_dotenv
from datetime import timedelta
from backend.database import db
from sqlalchemy import text 
from flask_migrate import Migrate
from backend.models.organisation import Organisation
from backend.models.user import User
from backend.models.property import Property
from backend.models.tenant import Tenant
from backend.models.maintenance_request import MaintenanceRequest
from backend.routes.organisations import organisations_bp
from backend.routes.users import users_bp
from backend.models.audit_log import AuditLog
from backend.routes.auth import auth_bp
from flask_jwt_extended import JWTManager
from backend.routes.properties import property_bp
from backend.routes.tenants import tenant_bp
from backend.routes.maintenance import maintenance_bp
from backend.routes.task_assignments import task_assignment_bp
load_dotenv()
app=flask.Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)
jwt = JWTManager(app)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
db.init_app(app)
migrate = Migrate(app, db)
app.register_blueprint(organisations_bp)
app.register_blueprint(property_bp)
app.register_blueprint(users_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(tenant_bp)
app.register_blueprint(maintenance_bp)
app.register_blueprint(task_assignment_bp)
@app.route("/")
def home():
    return os.getenv("APP_NAME")

with app.app_context():
    result=db.session.execute(text("SELECT 1"))
    print(result.scalar())

if __name__=="__main__":
    app.run()
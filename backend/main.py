import flask
import os
from dotenv import load_dotenv
from backend.database import db
from sqlalchemy import text 
from flask_migrate import Migrate
from backend.models.organisation import Organisation
from backend.models.user import User
from backend.models.property import Property
from backend.models.tenant import Tenant
from backend.models.maintenance_request import MaintenanceRequest
from backend.routes.organisations import organisations_bp
from backend.models.task_assignment import TaskAssignment
load_dotenv()
app=flask.Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
db.init_app(app)
migrate = Migrate(app, db)
app.register_blueprint(organisations_bp)

@app.route("/")
def home():
    return os.getenv("APP_NAME")

with app.app_context():
    result=db.session.execute(text("SELECT 1"))
    print(result.scalar())

if __name__=="__main__":
    app.run()
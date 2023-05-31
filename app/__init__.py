from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

application = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
application.config['SQLALCHEMY_DATABASE_URI'] = ("sqlite:///" + os.path.join(
                                                      basedir, "store.db"))
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
application.secret_key = "Lmleo783L!sl"
db = SQLAlchemy(application)

from app.models import Category, Manufacturer, Product, ProductSaleDate
from app import views, models

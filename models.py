# -*- coding: utf-8 -*-

from hello import db

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # поиск по этому полю
    name_eng = db.Column(db.String(100), nullable=True)
    manufacturers = db.relationship('Manufacturer', backref='category', cascade='all, delete-orphan')

class Manufacturer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # поиск по этому полю
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    products = db.relationship('Product', backref='manufacturer', cascade='all, delete-orphan')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False) # поиск по этому полю
    sku = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(200)) # поиск по этому полю
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    last_updated = db.Column(db.DateTime, nullable=False)
    color = db.Column(db.String(50), nullable=True)
    fct_type = db.Column(db.String(20), nullable=True)
    fct_fltr = db.Column(db.Boolean, nullable=True)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('manufacturer.id', ondelete='CASCADE'), nullable=False)

class ProductSaleDate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id', ondelete='CASCADE'), nullable=False)
    sale_date = db.Column(db.Date, nullable=False)
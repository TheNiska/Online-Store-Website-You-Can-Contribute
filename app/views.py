# -*- coding: utf-8 -*-
from app import application, db
from app.models import Category, Manufacturer, Product, ProductSaleDate
from flask import (Flask, render_template, request, redirect, url_for, flash,
                   make_response, current_app, jsonify)
from functools import wraps
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
import pytz
from sqlalchemy import or_, and_, func
from bs4 import BeautifulSoup
import csv
from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField
from wtforms.validators import DataRequired
import os
tz = pytz.timezone('Europe/Moscow')


@application.context_processor
def inject_data():
    categories = Category.query.all()
    manufacturers = Manufacturer.query.all()
    manufacturers_set = set()
    for manufacturer in manufacturers:
        manufacturers_set.add(manufacturer.name)

    if 'liked_products' in request.cookies:
        liked_products = request.cookies.get('liked_products')
        liked_products_list = liked_products.split(',')
    else:
        liked_products_list = []

    return dict(categories=categories, manufacturers_set=manufacturers_set,
                liked_products=liked_products_list)


# ----------функции для скачивания таблицы-----------------
def get_table_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')

    # Получаем заголовки
    is_less_then_seven = False
    headers = table.find_all('th')

    if len(headers) < 7:
        is_less_then_seven = True

    header_data = [header.get_text() for header in headers]

    if not is_less_then_seven:
         del header_data[-1]

    rows = table.find_all('tr')[1:] # пропустаем первую строку, иначе ошибка
    table_data = []
    for row in rows:
        cells = row.find_all('td')
        row_data = [cell.get_text() for cell in cells]
        if not is_less_then_seven:
            del row_data[6] # удаление 7-го столбца
        row_data[4] = cells[4].find('span', class_='product_quantity').get_text() # извлечение данных из тега span в 5-м столбце
        table_data.append(row_data)

    table_data.insert(0, header_data)

    return table_data

@application.route('/download_csv', methods=['POST'])
def download_csv():
    html = request.form['html']
    table_data = get_table_data(html)
  
    # Сохраняем данные в файл
    with open('tab.csv', 'w', newline='', encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerows(table_data)


    # Отправляем файл клиенту
    with open('tab.csv', 'r', newline='', encoding="utf-8-sig") as f:
        csv_data = f.read()

    response = make_response(csv_data)
    response.headers['Content-Disposition'] = 'attachment; filename=table.csv'
    response.headers['Content-type'] = 'text/csv; charset=utf-8-sig'
    return response
# конец функция для скачивания таблицы ---------------------------------------------------



@application.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')



@application.route('/search', methods=['POST'])
def search():
    form_id = request.form.get("form_id")
    results = []
    search_term = ""

    if form_id == "extended-search":
        category_id = request.form["category"]
        manufacturer_name = request.form["manufacturer"]
        name_term = request.form["name_term"].lower().strip()
        descr_term = request.form["descr_term"].lower().strip()

        if category_id == "5":
            fct_type = request.form["fct_type"]
            color = request.form["color"].lower().strip()

            products = Product.query.join(Manufacturer).join(Category).\
                   filter(or_(Category.id == category_id, not category_id)).\
                   filter(or_(Manufacturer.name == manufacturer_name, not manufacturer_name)).\
                   filter(and_(Product.fct_type.like(f'%{fct_type}%'), 
                               Product.color.like(f'%{color}%'),
                               or_(Product.name.like(f'%{name_term}%'), Product.sku.like(f'%{name_term}%')),
                               Product.description.like(f'%{descr_term}%'))).all()
        else:
            print("Поиск всех продуктов")
            products = Product.query.join(Manufacturer).join(Category).\
                       filter(or_(Category.id == category_id, not category_id)).\
                       filter(or_(Manufacturer.name == manufacturer_name, not manufacturer_name)).\
                       filter(or_(Product.name.like(f'%{name_term}%'), Product.sku.like(f'%{name_term}%')),
                                   Product.description.like(f'%{descr_term}%')).all()

        search_term = name_term + " " + descr_term
        results = products

    return render_template('search_results_squares.html', results=results, search_term=search_term, int=int)


@application.route('/products/<int:manufacturer_id>/<string:category_name>')
def products(manufacturer_id, category_name):
    table = request.args.get('table')
    manufacturer = Manufacturer.query.get(manufacturer_id)
    products = Product.query.filter_by(manufacturer_id=manufacturer_id).all()
    if table == "True":
        return render_template('products.html', manufacturer=manufacturer,
                                products=products, category_name=category_name)
    else:
        return render_template('products_squares.html', manufacturer=manufacturer,
                                products=products, category_name=category_name, int=int)

@application.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    category_name = request.args.get('category_name')
    product = Product.query.filter_by(id=product_id).first_or_404()
    if request.method == 'POST':
        category_name = request.form['category_name']
        old_price = float(request.form['old_price'])
        product.name = request.form['name'].lower().strip()
        product.sku = request.form['sku'].lower().strip()
        product.material = request.form['material'].lower().strip()
        product.color = request.form['color'].lower().strip()
        product.description = request.form['description'].lower().strip()
        product.price = float(request.form['price'])
        if product.price != old_price:
            product.last_updated = datetime.now(tz)
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products', manufacturer_id=product.manufacturer_id, category_name=category_name ))
    else:
        return render_template('edit_product.html', product=product, category_name=category_name)


@application.route('/add_product/<int:manufacturer_id>', methods=['POST'])
def add_product(manufacturer_id):
    category_name = request.form['category_name']
    name = request.form['name'].lower().strip()
    sku = request.form['sku'].lower().strip()
    description = request.form['description'].lower().strip()
    price = request.form['price']
    quantity = request.form['quantity']
    last_updated = datetime.now(tz)

    if category_name == "mixers":
        color = request.form['color'].lower()
        fct_type = request.form['fct_type'].lower()
        
        if 'fct_fltr' in request.form:
            fct_fltr_checked = request.form['fct_fltr']
        else:
            fct_fltr_checked = "off"

        if fct_fltr_checked == "on":
            fct_fltr = True
        else:
            fct_fltr = False
        product = Product(name=name, sku=sku, description=description, price=price, quantity=quantity,
                          manufacturer_id=manufacturer_id, last_updated=last_updated, color=color,
                          fct_type=fct_type, fct_fltr=fct_fltr)
    else:
        product = Product(name=name, sku=sku, description=description, price=price, quantity=quantity,
                          manufacturer_id=manufacturer_id, last_updated=last_updated)
    db.session.add(product)
    db.session.commit()
    flash('Product added successfully')
    return redirect(url_for('products', manufacturer_id=manufacturer_id, category_name=category_name))

@application.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'success': True})


@application.route('/update_quantity/<int:product_id>', methods=['POST'])
def update_quantity(product_id):
    product = Product.query.get(product_id)
    quantity_tmp = product.quantity
    category_name = request.form['category_name']
    action = request.form['action']
    if action == '+':
        product.quantity += 1
        quantity_tmp = product.quantity
    elif action == 'del':
        product.quantity -= 1
        quantity_tmp = product.quantity
    elif action == '-':
        product.quantity -=1
        quantity_tmp = product.quantity
        date = request.form['sale_date']
        sale_date = datetime.strptime(date, '%Y-%m-%d').date()
        product_sale_date = ProductSaleDate(product_id=product.id, sale_date=sale_date)
        db.session.add(product_sale_date)
    db.session.commit()
    return jsonify({'success': True, 'quantity_tmp': quantity_tmp})


@application.route('/manufacturers/<int:category_id>')
def manufacturers(category_id):
    manufacturers = Manufacturer.query.filter_by(category_id=category_id).all()
    category = Category.query.filter_by(id=category_id).first()
    return render_template('manufacturers.html', manufacturers=manufacturers, category=category)


@application.route('/add_manufacturer/<int:category_id>', methods=['POST'])
def add_manufacturer(category_id):
    name = request.form['name']
    category_id = request.form['category_id']
    manufacturer = Manufacturer(name=name, category_id=category_id)
    db.session.add(manufacturer)
    db.session.commit()
    flash('Manufacturer added successfully')
    return redirect(url_for('manufacturers', category_id=category_id))


@application.route('/like/<int:product_id>', methods=['POST'])
def like(product_id):
    response = ''
    if 'liked_products' in request.cookies:
        liked_products = request.cookies.get('liked_products')
        liked_products_list = liked_products.split(',')
        if str(product_id) in liked_products_list:
            liked_products_list.remove(str(product_id))
            response = 'removed'
        else:
            liked_products_list.append(str(product_id))
            response = 'added'
        liked_products = ','.join(liked_products_list)
    else:
        liked_products = str(product_id)
        response = 'added'

    resp = make_response(jsonify({'result': response, 'liked_products': liked_products}))
    resp.set_cookie('liked_products', liked_products)
    return resp
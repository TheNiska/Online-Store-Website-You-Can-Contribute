# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, redirect, url_for, flash, make_response
from functools import wraps
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import pytz
from sqlalchemy import or_
from bs4 import BeautifulSoup
import csv


application = Flask(__name__)
application.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///store.db'
application.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
application.secret_key = "Lmleo783L!sl"
PASSWORD = "PFdmn1717"
db = SQLAlchemy(application)

tz = pytz.timezone('Europe/Moscow')


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    name_eng = db.Column(db.String(100), nullable=True)
    manufacturers = db.relationship('Manufacturer', backref='category', cascade='all, delete-orphan')

class Manufacturer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    products = db.relationship('Product', backref='manufacturer', cascade='all, delete-orphan')

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sku = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(200))
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



# В этой функции мы проверяем авторизован ли пользователь перед заходом на любую страницу
@application.before_request
def check_auth():
    if not request.cookies.get('auth') and request.endpoint != 'login':
        return redirect(url_for('login'))

def check_password(password):
    return password == PASSWORD


#----------функции для скачивания таблицы-----------------
def get_table_data(html):
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find('table')

    # Получаем заголовки
    headers = table.find_all('th')
    header_data = [header.get_text() for header in headers]
    del header_data[-1]

    rows = table.find_all('tr')[1:] # пропустаем первую строку, иначе ошибка
    table_data = []
    for row in rows:
        cells = row.find_all('td')
        row_data = [cell.get_text() for cell in cells]
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



@application.route('/')
def index():
    categories = Category.query.all()
    return render_template('index.html', categories=categories)

@application.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form['password']
        if check_password(password):
            # Устанавливаем cookie-файл с помощью функции make_response
            resp = make_response(redirect(url_for('index')))
            resp.set_cookie('auth', 'true')
            return resp
        else:
            flash('Неверный пароль')
    return render_template('login.html')

@application.route('/logout')
def logout():
    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('auth', '', expires=0)
    return resp

@application.route('/search', methods=['POST'])
def search():
    search_term = request.form['search_term'].lower()
    results = Product.query.filter(or_(Product.name.ilike('%' + search_term + '%'),
                                       Product.name.ilike('%' + search_term.capitalize() + '%'),
                                       Product.name.ilike('%' + search_term.upper() + '%'),
                                       Product.sku.ilike('%' + search_term + '%'),
                                       Product.sku.ilike('%' + search_term.capitalize() + '%'),
                                       Product.sku.ilike('%' + search_term.upper() + '%'),
                                       Product.description.ilike('%' + search_term + '%'),
                                       Product.description.ilike('%' + search_term.capitalize() + '%'),
                                       Product.description.ilike('%' + search_term.upper() + '%'),
                                      ))

    return render_template('search_results.html', results=results, search_term=search_term)


@application.route('/products/<int:manufacturer_id>/<string:category_name>')
def products(manufacturer_id, category_name):
    if request.method == 'POST':
        form_id = request.form.get("form_id")
        if form_id == "print_form":
            html_table()
    manufacturer = Manufacturer.query.get(manufacturer_id)
    products = Product.query.filter_by(manufacturer_id=manufacturer_id).all()
    return render_template('products.html', manufacturer=manufacturer, products=products, category_name=category_name)

@application.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    category_name = request.args.get('category_name')
    product = Product.query.filter_by(id=product_id).first_or_404()
    if request.method == 'POST':
        product.name = request.form['name']
        product.sku = request.form['sku']
        product.description = request.form['description']
        product.price = request.form['price']
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products', manufacturer_id=product.manufacturer_id, category_name=category_name ))
    else:
        return render_template('edit_product.html', product=product, category_name=category_name)

@application.route('/update_product/<int:product_id>', methods=['GET', 'POST'])
def update_product(product_id):
    product = Product.query.filter_by(id=product_id).first_or_404()
    if request.method == 'POST':
        category_name = request.form['category_name']
        old_price = float(request.form['old_price'])
        product.name = request.form['name']
        product.sku = request.form['sku']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        if product.price != old_price:
            product.last_updated = datetime.now(tz)
        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products', manufacturer_id=product.manufacturer_id, category_name=category_name))
    else:
        return render_template('edit_product.html', product=product, category_name=category_name)

@application.route('/add_product/<int:manufacturer_id>', methods=['POST'])
def add_product(manufacturer_id):
    category_name = request.form['category_name']
    name = request.form['name']
    sku = request.form['sku']
    description = request.form['description']
    price = request.form['price']
    quantity = request.form['quantity']
    last_updated = datetime.now(tz)

    if category_name == "mixers":
        color = request.form['color']
        fct_type = request.form['fct_type']
        
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
    category_name = request.form['category_name']
    product = Product.query.get(product_id)
    manufacturer_id = product.manufacturer_id
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully')
    return redirect(url_for('products', manufacturer_id=manufacturer_id, category_name=category_name))

@application.route('/update_quantity/<int:product_id>', methods=['POST'])
def update_quantity(product_id):
    product = Product.query.get(product_id)
    category_name = request.form['category_name']
    action = request.form['action']
    if action == '+':
        product.quantity += 1
    elif action == 'del':
        product.quantity -= 1
    elif action == '-':
        product.quantity -=1
        date = request.form['sale_date']
        sale_date = datetime.strptime(date, '%Y-%m-%d').date()
        product_sale_date = ProductSaleDate(product_id=product.id, sale_date=sale_date)
        db.session.add(product_sale_date)


    db.session.commit()
    flash('Product quantity updated successfully')
    return redirect(url_for('products', manufacturer_id=product.manufacturer_id, category_name=category_name))


@application.route('/manufacturers/<int:category_id>')
def manufacturers(category_id):
    manufacturers = Manufacturer.query.filter_by(category_id=category_id).all()
    category = Category.query.filter_by(id=category_id).first()
    return render_template('manufacturers.html', manufacturers=manufacturers, category=category)


@application.route('/dates/<int:product_id>', methods=['GET'])
def dates(product_id):
    product = Product.query.get(product_id)
    sales_dates = ProductSaleDate.query.filter_by(product_id=product_id).all()
    return render_template('sold_dates.html', sales_dates=sales_dates, product=product, len=len)

@application.route('/add_manufacturer/<int:category_id>', methods=['POST'])
def add_manufacturer(category_id):
    name = request.form['name']
    category_id = request.form['category_id']
    manufacturer = Manufacturer(name=name, category_id=category_id)
    db.session.add(manufacturer)
    db.session.commit()
    flash('Manufacturer added successfully')
    return redirect(url_for('manufacturers', category_id=category_id))

@application.route('/delete_manufacturer/<int:id>', methods=['POST'])
def delete_manufacturer(id):
    manufacturer = Manufacturer.query.get(id)
    category_id = manufacturer.category_id
    db.session.delete(manufacturer)
    db.session.commit()
    flash('Manufacturer deleted successfully')
    return redirect(url_for('manufacturers', category_id=category_id))


@application.route('/add_category', methods=['POST'])
def add_category():
    name = request.form['name']
    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    return redirect(url_for('index'))

@application.route('/delete_category/<int:category_id>', methods=['POST'])
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id).first()
    db.session.delete(category)
    db.session.commit()
    return redirect(url_for('index'))

@application.route('/amount_change', methods=['GET', 'POST'])
def amount_change():
    message = ""

    if request.method == 'POST':
        form_id = request.form.get("form_id")

        if form_id == "search_form":
            sku = request.form['sku']
            # ищем товар в базе данных
            product = Product.query.filter_by(sku=sku).first()
            if product:
                return render_template('amount.html', product=product)
            else:
                message = "Такого продукта нет"
                return render_template('amount.html', message=message)

        elif form_id == "change_form":
            sku = request.form['sku']
            product = Product.query.filter_by(sku=sku).first()
            if product:
                product.quantity = request.form['quantity']
                db.session.commit()
                message = "Количество товара успешно изменено"
                return render_template('amount.html', message=message)
            else:
                message = "Ошибка: товар не найден по артикулу"
                return render_template('amount.html', message=message)

    return render_template('amount.html', message=message)


@application.before_first_request
def create_tables():
    db.create_all()

if __name__ == "__main__":
   application.run(host='0.0.0.0')

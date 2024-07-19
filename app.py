from flask import Flask, render_template,request,redirect,Response,url_for,jsonify, flash,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime,date,timedelta
from decimal import Decimal
import csv
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.palettes import Category20c
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import json
import plotly
import pandas as pd
from io import StringIO
import random
import string
import hashlib
import uuid
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError



# Initialize Flask app
app = Flask(__name__)

# Set the secret key
app.secret_key = 'AVA_SOY'

external_stylesheets = ['https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css','/static/css/navbar.css','/static/css/card.css']
dash_app = Dash(__name__, external_stylesheets=external_stylesheets,server=app, url_base_pathname='/variousinsights/')


# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def table_to_dataframe(table):
    with app.app_context():
        records = table.query.all()
        data = [{column.name: getattr(record, column.name) for column in table.__table__.columns} for record in records]
        return pd.DataFrame(data)

# Define database models
class Customer(db.Model):
    CustomerID = db.Column(db.String(60), primary_key=True)
    CustomerName = db.Column(db.String(255))
    Address = db.Column(db.String(255))
    ContactPerson = db.Column(db.String(255))
    ContactNumber = db.Column(db.String(20))
    EmailId=db.Column(db.String(50))
    CustomerType = db.Column(db.Enum('Individual', 'Shop'))
    GSTRegistered = db.Column(db.Boolean)
    GSTNumber = db.Column(db.String(20))
    EngagementSource = db.Column(db.Enum('Direct', 'Marketing', 'Digital Media'))
    FirstOrderDate = db.Column(db.Date)
    LastOrderDate = db.Column(db.Date)
    LastBillNumber = db.Column(db.String(20))
    LastOrderID = db.Column(db.Integer)
    TotalCredit = db.Column(db.Float)
    TotalBusinessAmount = db.Column(db.Float)
    TotalTofuOrdered = db.Column(db.Float)
    TotalTofuAmount = db.Column(db.Float)
    TotalMilkOrdered = db.Column(db.Float)
    TotalMilkAmount = db.Column(db.Float)
    # Status = db.Column(db.Enum('Active', 'Obsolete'))
    CrateGiven = db.Column(db.Integer)
    # CrateReceived = db.Column(db.Integer)

class Production(db.Model):
    ProductionID = db.Column(db.String(60), primary_key=True)
    BatchID = db.Column(db.String(20))
    ProductID = db.Column(db.String(60), db.ForeignKey('product.ProductID'))
    # ProductID = db.Column(db.String(60))
    ManufacturingDate = db.Column(db.Date)
    ManufacturedQuantity = db.Column(db.Float)
    BeansQuantity = db.Column(db.Integer)
    # ManufacturedTime = db.Column(db.Time)
    ManufacturedOrNot = db.Column(db.Boolean)
    comments = db.Column(db.String(500))

class Orders(db.Model):
    OrderID = db.Column(db.String(60), primary_key=True)
    BillID = db.Column(db.Integer)
    # CustomerID = db.Column(db.Integer, db.ForeignKey('customer.CustomerID'))
    # ProductID = db.Column(db.Integer, db.ForeignKey('product.ProductID'))
    CustomerID = db.Column(db.String(60), db.ForeignKey('customer.CustomerID'))
    ProductID = db.Column(db.String(60), db.ForeignKey('product.ProductID'))
    BatchID = db.Column(db.String(20))
    Quantity = db.Column(db.Integer)
    Amount = db.Column(db.Float)
    OrderDateTime = db.Column(db.DateTime)
    PaymentType = db.Column(db.Enum('Online', 'Cash','Credit'))
    PaymentReceivedOrNot = db.Column(db.Boolean)
    CratesGiven = db.Column(db.Integer)
    PreferredOrderDate = db.Column(db.Date)
    ActualOrderDeliveredDate = db.Column(db.Date)
    DeliveryPersonID = db.Column(db.String(60), db.ForeignKey('delivery_person.DeliveryPersonID'))
    # DeliveryPersonID = db.Column(db.Integer, db.ForeignKey('delivery_person.DeliveryPersonID'))
    DeliveredOrNot = db.Column(db.Boolean)
   
class Product(db.Model):
    ProductID = db.Column(db.String(60), primary_key=True) 
    ProductName = db.Column(db.String(255))
    Type = db.Column(db.Enum('Tofu', 'Milk'))
    SugarType = db.Column(db.String(50))
    ProductDescription = db.Column(db.String(255))
    Price = db.Column(db.Float)
    AvailableQuantity = db.Column(db.Integer)
    TotalQuantityProduced = db.Column(db.Integer)
    AvailableOrNot = db.Column(db.Boolean)

class DeliveryPerson(db.Model):
    DeliveryPersonID = db.Column(db.String(60), primary_key=True)
    DeliveryPersonName = db.Column(db.String(255))
    ContactNumber = db.Column(db.String(20))
    TotalDeliveries = db.Column(db.Integer)
    PreferredDeliveryLocations = db.Column(db.String(255))
    ActiveOrObsolete = db.Column(db.Boolean)

class Inventory_General(db.Model):
    Inventory_General_ID = db.Column(db.String(60), primary_key=True)
    RawMaterialName = db.Column(db.String(255))
    AvailableQuantity = db.Column(db.Float)
    Need_to_buy = db.Column(db.Boolean)

class Inventory_Milk(db.Model):
    Inventory_Milk_Id = db.Column(db.String(60), primary_key=True)
    Milk_Inventory_type = db.Column(db.Enum('Essence', 'Color'))
    Milk_Inventory_name = db.Column(db.String(255))
    Milk_Inventory_quantity = db.Column(db.Integer)
    # Need_to_buy = db.Column(db.Boolean)

class Inventory_Tofu(db.Model):
    Inventory_Tofu_Id = db.Column(db.String(60), primary_key=True)
    Tofu_Inventory_name = db.Column(db.String(255))
    Tofu_Inventory_quantity = db.Column(db.Integer)
    # Need_to_buy = db.Column(db.Boolean)

class RawMaterialVendor(db.Model):
    VendorID = db.Column(db.String(60), primary_key=True)
    VendorName = db.Column(db.String(255))
    VendorPhoneNumber = db.Column(db.String(20))
    VendorAddress = db.Column(db.String(255))

class InventoryPurchase(db.Model):
    PurchaseID = db.Column(db.String(60), primary_key=True)
    #RawMaterialID = db.Column(db.Integer, db.ForeignKey('raw_material.RawMaterialID'))
    InventoryName = db.Column(db.String(255))
    VendorID = db.Column(db.String(60), db.ForeignKey('raw_material_vendor.VendorID')) #
    PurchaseDate = db.Column(db.Date)
    # Address = db.Column(db.String(255))
    # PhoneNumber = db.Column(db.String(20))
    Rate = db.Column(db.Float)
    Amount = db.Column(db.Float)
    PurchasedQuantity = db.Column(db.Integer)
    RemainingQuantity = db.Column(db.Integer)
    
class Sticker(db.Model):
    StickerID = db.Column(db.String(60), primary_key=True)
    Type = db.Column(db.Enum('Tofu', 'Milk')) 
    Flavour_name = db.Column(db.String(255))
    SugarType = db.Column(db.String(20))  
    AvailableQuantity = db.Column(db.Integer)

class Users(db.Model):
    User_ID=db.Column(db.String(255))
    User_fullname=db.Column(db.String(255))
    User_Address=db.Column(db.String(255))
    User_phone=db.Column(db.String(20))
    User_email=db.Column(db.String(100),unique=True)
    User_password=db.Column(db.String(20))
    UserName=db.Column(db.String(30), primary_key=True)
    User_Designation=db.Column(db.Enum("Production Manager", "Delivery Person","Admin","Order Manager"))




    


# Function to create default entries in the database
def create_default_entries():
    # Check if there are any entries in the Inventory_General table
    existing_entries = Inventory_General.query.all()
    if not existing_entries:
        # Create a default entry for "Sugar" if the table is empty
        raw_material_name="Sugar"
        general_id = 'RG'
        general_id += raw_material_name[:3].upper()
        general_id += ''.join(random.choices(string.digits, k=7)) 
        default_sugar = Inventory_General(
            Inventory_General_ID=general_id,
            RawMaterialName="Sugar",
            AvailableQuantity=0,
            Need_to_buy=True
        )
        db.session.add(default_sugar)
        db.session.commit()

def calculate_revenue_and_pending_amount(orders_df):
    # Filter delivered orders within the last one year
    one_year_ago = datetime.now() - timedelta(days=365)
    orders_df['ActualOrderDeliveredDate'] = pd.to_datetime(orders_df['ActualOrderDeliveredDate'])
    delivered_last_year = orders_df[(orders_df['DeliveredOrNot'] == True) & 
                                     (orders_df['ActualOrderDeliveredDate'] >= one_year_ago)]
    total_revenue_last_year = delivered_last_year['Amount'].sum()
    
    # Filter pending orders (credit or not delivered)
    pending_orders = orders_df[(orders_df['PaymentType'] == 'Credit') | 
                               (orders_df['DeliveredOrNot'] == False)]
    total_pending_amount = pending_orders['Amount'].sum()
    
    return total_revenue_last_year, total_pending_amount

def calculate_revenue_and_pending_amount_one_month(orders_df):
    one_year_ago = datetime.now() - timedelta(days=30)
    orders_df['ActualOrderDeliveredDate'] = pd.to_datetime(orders_df['ActualOrderDeliveredDate'])
    delivered_last_year = orders_df[(orders_df['DeliveredOrNot'] == True) & 
                                     (orders_df['ActualOrderDeliveredDate'] >= one_year_ago)]
    total_revenue_last_year = delivered_last_year['Amount'].sum()
    
    # Filter pending orders (credit or not delivered)
    pending_orders = orders_df[(orders_df['PaymentType'] == 'Credit') | 
                               (orders_df['DeliveredOrNot'] == False)]
    total_pending_amount = pending_orders['Amount'].sum()
    
    return total_revenue_last_year, total_pending_amount



with app.app_context():
    db.create_all()    
    create_default_entries() 

@app.route('/',methods=["GET","POST"])
def login():
    if request.method=="POST":
        username=request.form['id']
        password=request.form['password']
        user = Users.query.filter_by(UserName=username).first()
        if user.UserName==username and user.User_password==password:
            session['LoggedIn']=True
            session['Designation']=user.User_Designation

            if session['Designation']=="Admin":
                return render_template('dashboard.html')
            elif  session['Designation']=="Delivery Person":
                session['id']=user.User_ID
                return redirect('/deliveryInterface')
            elif session['Designation']=="Production Manager":
                return render_template('dashboard2.html')
            else:
                return render_template('dashboard3.html')
        else:
            return  "Invalid Username or Password"
        
    return render_template('login.html')       

################################################################## Product

@app.route('/product',methods=["GET","POST"])
def product():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        product=Product.query.all()    
        return render_template('product.html',products=product)
    

@app.route('/open_add_product')
def open_add_product():    
    return render_template("addProduct.html")

@app.route('/add_product', methods=["GET", "POST"])
def add_product():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        if request.method == "POST":
            product_name = request.form['productName']
            price = request.form['price']
            product_type = request.form['productType']
            sugar_type = request.form['sugarType']
            # available_quantity = request.form['availableQuantity']
            # total_quantity_produced = request.form['totalQuantityProduced']
            product_description = request.form['productDescription']
            available_or_not = True if request.form.get('availableOrNot') == 'on' else False

            # Check if the product already exists
            existing_product = Product.query.filter_by(ProductName=product_name, Type=product_type, SugarType=sugar_type).first()

            if existing_product:
                flash('error: Product already exists!')
                return redirect("/product")
            else:
                def generate_product_id(product_name, product_type, sugar_type):
                    # Extract initials of product_type and sugar_type
                    product_type_initial = product_type[0].upper()
                    sugar_type_initial = sugar_type[0].upper() if sugar_type else 'N'
                    
                    # Extract first three letters of product_name
                    product_name_short = product_name[:3].upper()
                    
                    # Generate random three-digit number
                    random_number = '{:03d}'.format(random.randint(0, 999))
                    
                    # Combine all parts to form the product ID
                    product_id = f"P{product_type_initial}{sugar_type_initial}{product_name_short}{random_number}"
                    
                    return product_id

                product_id = generate_product_id(product_name, product_type, sugar_type)
                

                new_product = Product(ProductID=product_id,
                                    ProductName=product_name,
                                    Price=price,
                                    Type=product_type,
                                    SugarType=sugar_type,
                                    AvailableQuantity=0,
                                    TotalQuantityProduced=0,
                                    ProductDescription=product_description,
                                    AvailableOrNot=available_or_not
                                    )

                db.session.add(new_product)
                db.session.commit()

                flash('success: Product added successfully!')
                return redirect("/product")
        
    # @app.route('/delete_product/<string:ProductID>')
    # def delete_product(ProductID):
    #     product=Product.query.filter_by(ProductID=ProductID).first()
    #     db.session.delete(product)
    #     db.session.commit()
    #     return redirect("/product")    

@app.route('/delete_product/<string:ProductID>')
def delete_product(ProductID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        product = Product.query.filter_by(ProductID=ProductID).first()
        if product:
            # Check if the product is referenced in the Production table
            production_count = Production.query.filter_by(ProductID=ProductID).count()
            production_count+= Orders.query.filter_by(ProductID=ProductID).count()
            if production_count > 0:
                # If referenced, prevent deletion and show a flash message
                flash("error: Cannot delete product because it is referenced in other records.")
            else:
                # If not referenced, proceed with deletion
                db.session.delete(product)
                db.session.commit()
                flash("success: Product deleted successfully.")
        return redirect("/product") 

@app.route('/open_update_product/<string:ProductID>')
def open_update_product(ProductID): 
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):      
        product=Product.query.filter_by(ProductID=ProductID).first()
        return render_template("updateProduct.html",product=product)

@app.route('/update_product/<string:ProductID>', methods=["GET", "POST"])
def update_product(ProductID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):   
        if request.method == "POST":
            # Fetch data from the form
            product_name = request.form["productName"]
            price = request.form["price"]
            product_type = request.form["productType"]
            sugar_type = request.form["sugarType"]
            available_quantity = request.form["availableQuantity"]
            # total_quantity_produced = request.form["totalQuantityProduced"]
            product_description = request.form['productDescription']
            available_or_not = True if request.form.get("availableOrNot") else False

            # Update product logic here
            product=Product.query.filter_by(ProductID=ProductID).first()
            product.ProductName = product_name
            product.Price = price
            product.Type = product_type
            product.SugarType = sugar_type
            product.AvailableQuantity = available_quantity
            # product.TotalQuantityProduced = total_quantity_produced
            product.ProductDescription = product_description
            product.AvailableOrNot = available_or_not

            # Commit changes to the database
            db.session.commit()

            # Redirect to product page after updating
            return redirect("/product")
    

@app.route('/download_products_csv')
def download_products_csv():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):   
        products = Product.query.all()
        
        # Create a CSV string
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Product ID', 'Product Name', 'Type', 'Sugar Type', 'Description', 'Price', 'Available Quantity', 'Total Quantity Produced', 'Available'])
        for product in products:
            writer.writerow([product.ProductID, product.ProductName, product.Type, product.SugarType, product.ProductDescription, product.Price, product.AvailableQuantity, product.TotalQuantityProduced, "Yes" if product.AvailableOrNot else "No"])

        # Set up the response headers
        output.seek(0)
        date_str = datetime.now().strftime("%d-%m-%Y")
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=products_{date_str}.csv"}
        )

    
################################################################## Orders

@app.route('/orders', methods=["GET", "POST"])
def orders():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Order Manager"):
        orders = Orders.query.all()
        product=Product.query.all()
        customers=Customer.query.all()  
        delivery_people = DeliveryPerson.query.all()
        return render_template('orders.html', orders=orders,products=product,customers=customers,delivery_people=delivery_people)

# @app.route('/open_add_order')
# def open_add_order():  
#     if session['LoggedIn'] == True and (session['Designation'] == "Admin" or session['Designation'] == "Order Manager"):
#         products = Product.query.all() 
#         customers = Customer.query.all()

#         # Retrieve the last used bill ID from the database
#         last_order = Orders.query.order_by(Orders.BillID.desc()).first()
#         if last_order:
#             last_bill_id = last_order.BillID
#             next_bill_id = int(last_bill_id) + 1
#         else:
#             next_bill_id = 1  # If no orders exist, start from 1

#         return render_template("addOrder.html", products=products, customers=customers, next_bill_id=next_bill_id)



# @app.route('/add_order', methods=["POST"])
# def add_order():
#     if session['LoggedIn'] == True and (session['Designation'] == "Admin" or session['Designation'] == "Order Manager"):
#         if request.method == "POST":
#             # Fetch data from the form
#             customer_id = request.form['customerID']
#             bill_id = request.form['billID']
#             payment_type = request.form['paymentType']
#             payment_received = True if request.form.get('paymentReceivedOrNot') == 'on' else False
#             preferred_order_date = datetime.strptime(request.form['preferredOrderDate'], '%Y-%m-%d')

#             # Create a list to store all new orders
#             new_orders = []

#             # Process each product in the form
#             for i in range(len(request.form.getlist('productID[]'))):
#                 product_id = request.form.getlist('productID[]')[i]
#                 quantity = request.form.getlist('quantity[]')[i]

#                 # Find the product object from the database
#                 product = Product.query.get(product_id)
#                 if product:
#                     amount = product.Price * int(quantity)

#                     # Generate unique order ID
#                     order_id = 'O' + customer_id[:2].upper() + product_id[:2] + payment_type[:2].upper() + ''.join(random.choices(string.digits, k=4))  # Random 4 digits

#                     new_order = Orders(
#                         OrderID=order_id,
#                         CustomerID=customer_id,
#                         ProductID=product_id,
#                         Quantity=quantity,
#                         Amount=amount,
#                         OrderDateTime=datetime.now(),
#                         PaymentType=payment_type,
#                         PaymentReceivedOrNot=payment_received,
#                         PreferredOrderDate=preferred_order_date,
#                         BillID=bill_id
#                     )

#                     new_orders.append(new_order)
#                 else:
#                     flash(f'error: Product with ID {product_id} does not exist!')
#                     return redirect("/add_order")

#             # Add all new orders to the session and commit
#             db.session.add_all(new_orders)
#             db.session.commit()

#             # Update customer information
#             customer = Customer.query.get(customer_id)
#             if customer:
#                 customer.LastBillNumber = bill_id
#                 customer.LastOrderDate = datetime.now().date()
#                 if customer.FirstOrderDate is None:
#                     customer.FirstOrderDate = datetime.now().date()

#                 db.session.commit()

#                 flash('success: Orders added successfully!')
#                 return redirect("/orders")
#             else:
#                 flash(f'error: Customer with ID {customer_id} does not exist!')
#                 return redirect("/add_order")





# Route to open add order page
@app.route('/open_add_order')
def open_add_order():  
    if session.get('LoggedIn') and (session.get('Designation') == "Admin" or session.get('Designation') == "Order Manager"):
        products = Product.query.all() 
        customers = Customer.query.all()

        # Retrieve the last used bill ID from the database
        last_order = Orders.query.order_by(Orders.BillID.desc()).first()
        if last_order:
            last_bill_id = last_order.BillID
            next_bill_id = int(last_bill_id) + 1
        else:
            next_bill_id = 1  # If no orders exist, start from 1

        return render_template("addOrder.html", products=products, customers=customers, next_bill_id=next_bill_id, date=date.today())

# Route to add order
@app.route('/add_order', methods=["POST"])
def add_order():
    if session.get('LoggedIn') and (session.get('Designation') == "Admin" or session.get('Designation') == "Order Manager"):
        if request.method == "POST":
            # Generate the bill number and date
            bill_number = request.form['billID']
            bill_date = date.today()

            # Fetch data from the form for adding the order
            customer_id = request.form['customerID']
            payment_type = request.form['paymentType']
            payment_received = True if request.form.get('paymentReceivedOrNot') == 'on' else False
            preferred_order_date = datetime.strptime(request.form['preferredOrderDate'], '%Y-%m-%d')

            # Create a list to store all new orders
            new_orders = []

            # Process each product in the form
            for i in range(len(request.form.getlist('productID[]'))):
                product_id = request.form.getlist('productID[]')[i]
                quantity = request.form.getlist('quantity[]')[i]

                # Find the product object from the database
                product = Product.query.get(product_id)
                if product:
                    amount = product.Price * int(quantity)

                    # Generate unique order ID
                    order_id = 'O' + customer_id[:2].upper() + product_id[:2] + payment_type[:2].upper() + ''.join(random.choices(string.digits, k=4))  # Random 4 digits

                    new_order = Orders(
                        OrderID=order_id,
                        CustomerID=customer_id,
                        ProductID=product_id,
                        Quantity=quantity,
                        Amount=amount,
                        OrderDateTime=datetime.now(),
                        PaymentType=payment_type,
                        PaymentReceivedOrNot=payment_received,
                        PreferredOrderDate=preferred_order_date,
                        BillID=bill_number
                    )

                    new_orders.append(new_order)
                else:
                    flash(f'error: Product with ID {product_id} does not exist!')
                    return redirect("/add_order")

            # Add all new orders to the session and commit
            db.session.add_all(new_orders)
            db.session.commit()

            # Update customer information
            customer = Customer.query.get(customer_id)
            if customer:
                customer.LastBillNumber = bill_number
                customer.LastOrderDate = datetime.now().date()
                if customer.FirstOrderDate is None:
                    customer.FirstOrderDate = datetime.now().date()

                db.session.commit()

                flash('success: Orders added successfully!')

                # Calculate total amount, GST, and final amount
                total_amount = sum(order.Amount for order in new_orders)
                gst_amount = total_amount * 0.05
                final_amount = total_amount + gst_amount

                products = Product.query.all()
                # Pass all the required information to the HTML template for displaying the bill
                return render_template("bill.html", bill_number=bill_number, bill_date=bill_date, customer=customer, orders=new_orders, total_amount=total_amount, gst_amount=gst_amount, final_amount=final_amount,products=products)
            else:
                flash(f'error: Customer with ID {customer_id} does not exist!')
                return redirect("/add_order")





@app.route('/delete_order/<string:OrderID>')
def delete_order(OrderID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Order Manager"):
        order = Orders.query.filter_by(OrderID=OrderID).first()
        db.session.delete(order)
        db.session.commit()
        flash("success: Order deleted successfully.")
        return redirect("/orders")


@app.route('/open_update_order/<string:OrderID>')
def open_update_order(OrderID):  
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Order Manager"):  
        order = Orders.query.filter_by(OrderID=OrderID).first()
        products=Product.query.all()
        customers=Customer.query.all()
        delivery_people = DeliveryPerson.query.all()
        return render_template("updateOrder.html", order=order,products=products,customers=customers,delivery_people=delivery_people)

@app.route('/update_order/<string:OrderID>', methods=["POST"])
def update_order(OrderID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Order Manager"):
        if request.method == "POST":
            # Fetch data from the form
            customer_id = request.form['customerID']
            product_id = request.form['productID']
            batch_id = request.form['batchID'] or None
            quantity = int(request.form['quantity'])
            # amount = float(request.form['amount']) if request.form['amount'] else None
            payment_type = request.form['paymentType']
            payment_received = True if request.form.get('paymentReceivedOrNot') == 'on' else False
            crates_given = int(request.form['cratesGiven']) if request.form['cratesGiven'] else 0
            delivery_person_id = request.form['deliveryPersonID'] if request.form['deliveryPersonID'] else None
            delivered = True if request.form.get('deliveredOrNot') == 'on' else False
            preferred_order_date = datetime.strptime(request.form['preferredOrderDate'], '%Y-%m-%d')
            actual_order_delivered_date_str = request.form.get('actualOrderDeliveredDate', None)
            actual_order_delivered_date = datetime.strptime(actual_order_delivered_date_str, '%Y-%m-%d') if actual_order_delivered_date_str else None
            bill_id = int(request.form['billID']) if request.form['billID'] else None

            products=Product.query.all()
            amount=0
            for product in products:
                if product_id==str(product.ProductID):
                    amount = product.Price * int(quantity)

                    
            orderx = Orders.query.all() 
            for orderxx in orderx:
                if orderxx.OrderID==OrderID:     
                    if delivered and not orderxx.DeliveredOrNot :
                        customers = Customer.query.all()
                        for product in products:
                            if product_id==str(product.ProductID):
                                product.AvailableQuantity-=quantity
                                for customer in customers:
                                    if customer_id==str(customer.CustomerID):
                                        customer.TotalCredit+=int(quantity)
                                        customer.CrateGiven+=crates_given
                                        customer.TotalBusinessAmount+=float(str(amount))
                                        if product.Type=='Tofu':
                                            customer.TotalTofuAmount+=float(str(amount))
                                            customer.TotalTofuOrdered+=quantity
                                        if product.Type=='Milk':
                                            customer.TotalMilkAmount+=float(str(amount))
                                            customer.TotalMilkOrdered+=quantity


                        delivery_people = DeliveryPerson.query.all()    
                        for people in delivery_people:
                            if delivery_person_id==str(people.DeliveryPersonID):
                                people.TotalDeliveries+=1

            

            # Update order logic here
            order = Orders.query.filter_by(OrderID=OrderID).first()
            order.CustomerID = customer_id
            order.ProductID = product_id
            order.BatchID = batch_id
            order.Quantity = quantity
            order.Amount = amount
            order.PaymentType = payment_type
            order.PaymentReceivedOrNot = payment_received
            order.CratesGiven = crates_given
            order.DeliveryPersonID = delivery_person_id
            order.DeliveredOrNot = delivered
            order.PreferredOrderDate = preferred_order_date
            order.ActualOrderDeliveredDate = actual_order_delivered_date
            order.BillID = bill_id

            # Commit changes to the database
            db.session.commit()

            # Redirect to orders page after updating
            return redirect("/orders")

@app.route('/download_orders_csv')
def download_orders_csv():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Order Manager"):
        orders = Orders.query.all()
        
        # Create a CSV string
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Order ID', 'Bill ID', 'Customer ID', 'Product ID', 'Batch ID', 'Quantity', 'Amount', 'Order DateTime', 'Payment Type', 'Payment Received', 'Crates Given', 'Preferred Order Date', 'Actual Order Delivered Date', 'Delivery Person ID', 'Delivered'])
        for order in orders:
            writer.writerow([order.OrderID, order.BillID, order.CustomerID, order.ProductID, order.BatchID, order.Quantity, order.Amount, order.OrderDateTime, order.PaymentType, "Yes" if order.PaymentReceivedOrNot else "No", order.CratesGiven, order.PreferredOrderDate, order.ActualOrderDeliveredDate, order.DeliveryPersonID, "Yes" if order.DeliveredOrNot else "No"])

        # Set up the response headers
        output.seek(0)
        date_str = datetime.now().strftime("%d-%m-%Y")
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=orders.csv_{date_str}"}
        )

@app.route('/generate_bill/<string:bill_number>', methods=["GET"])
def generate_bill(bill_number):
    # Fetch all orders with the provided bill number
    orders = Orders.query.filter_by(BillID=bill_number).all()
    if not orders:
        flash("error: No orders found for the specified bill number.")
        return redirect("/orders")

    # Fetch additional data needed for the bill (e.g., customer details)
    # This assumes that all orders in the bill belong to the same customer
    customer_id = orders[0].CustomerID  # Assuming all orders have the same customer ID
    customer = Customer.query.get(customer_id)

    # Calculate total amount for the bill
    total_amount = sum(order.Amount for order in orders)

    # Calculate GST (assuming 5%)
    gst_amount = total_amount * 0.05

    # Calculate final amount including GST
    final_amount = total_amount + gst_amount

    bill_date = date.today()
    products = Product.query.all()
    # Render the bill template with necessary data
    return render_template("bill.html",bill_number=bill_number, orders=orders,bill_date=bill_date, customer=customer, total_amount=total_amount, gst_amount=gst_amount, final_amount=final_amount,products=products)
    
################################################################## Production

# Routes for Production Section
@app.route('/production', methods=["GET", "POST"])
def production():
    print('hello')
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        productions = Production.query.all()
        products=Product.query.all()
        return render_template('production.html', productions=productions,products=products)
    print('bye')

@app.route('/open_add_production')
def open_add_production(): 
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
    #productions = Production.query.all()
        products=Product.query.all()
        return render_template("addProduction.html",products=products)

def generate_production_id(product_id, manufacturing_date):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
    # Extract initials of ProductID
        product_initial = product_id[:2].upper()

        # Extract last two digits of year from ManufacturingDate
        year_last_two_digits = str(manufacturing_date.year)[-2:]

        # Generate random four-digit number
        random_number = '{:04d}'.format(random.randint(0, 9999))

        # Combine all parts to form the production ID
        production_id = f"PR{product_initial}{year_last_two_digits}{random_number}"

        return production_id
    
def generate_batch_id(product_id, manufacturing_date):
    # Extract last two digits of year from Manufacturing Date
    year_last_two_digits = str(manufacturing_date.year)[-2:]

    # Extract month and day from Manufacturing Date
    month_day = manufacturing_date.strftime('%m%d')

    # Generate random three-digit number
    random_number = '{:03d}'.format(random.randint(0, 999))

    # Combine all parts to form the batch ID
    batch_id = f"BID{product_id}{year_last_two_digits}{month_day}{random_number}"

    return batch_id


@app.route('/add_production', methods=["POST"])
def add_production():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        if request.method == "POST":
            # Fetch data from the form
            product_id = request.form['productID']
            manufacturing_date = datetime.strptime(request.form['manufacturingDate'], '%Y-%m-%d')
            # batch_id = request.form['batchID']
            manufactured_quantity = request.form['manufacturedQuantity']
            # beans_quantity = request.form['beansQuantity']
            # manufactured_time = datetime.strptime(request.form['manufacturedTime'], '%H:%M').time()
            # manufactured_or_not = True if request.form.get('manufacturedOrNot') == 'on' else False
            comments = request.form['comments']
            batch_id = generate_batch_id(product_id, manufacturing_date)

            # Check if the production already exists
            existing_production = Production.query.filter_by(ProductID=product_id, ManufacturingDate=manufacturing_date).first()

            if existing_production:
                flash('error: Production already exists!')
                return redirect("/production")
            else:
                # Generate unique production ID
                production_id = generate_production_id(product_id, manufacturing_date)

                new_production = Production(ProductionID=production_id,
                                            ProductID=product_id,
                                            ManufacturingDate=manufacturing_date,
                                            BatchID=batch_id,
                                            # BatchID=batch_id,
                                            ManufacturedQuantity=manufactured_quantity,
                                            # BeansQuantity=beans_quantity,
                                            # ManufacturedTime=manufactured_time,
                                            # ManufacturedOrNot=manufactured_or_not,
                                            comments=comments)  # Corrected field name to lowercase 'comments'

                db.session.add(new_production)
                db.session.commit()

                flash('success: Production added successfully!')
                return redirect("/production")

@app.route('/delete_production/<string:ProductionID>')
def delete_production(ProductionID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        production = Production.query.filter_by(ProductionID=ProductionID).first()
        db.session.delete(production)
        db.session.commit()
        flash("success: Production deleted successfully.")
        return redirect("/production")

@app.route('/open_update_production/<string:ProductionID>')
def open_update_production(ProductionID): 
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):   
        production = Production.query.filter_by(ProductionID=ProductionID).first()
        products=Product.query.all()
        return render_template("updateProduction.html", production=production,products=products)

@app.route('/update_production/<string:ProductionID>', methods=["POST"])
def update_production(ProductionID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        if request.method == "POST":
            # Fetch data from the form
            product_id = request.form['productID']
            manufacturing_date = datetime.strptime(request.form['manufacturingDate'], '%Y-%m-%d')
            # batch_id = request.form['batchID']
            manufactured_quantity = float(request.form['manufacturedQuantity'])
            beans_quantity = request.form['beansQuantity']
            # manufactured_time_str = request.form.get('manufacturedTime')
            # manufactured_time = datetime.strptime(manufactured_time_str, '%H:%M').time() if manufactured_time_str else None
            manufactured_or_not = True if request.form.get('manufacturedOrNot') == 'on' else False
            comments = request.form['comments']
            batch_id = generate_batch_id(product_id, manufacturing_date)


            productionx = Production.query.all()
            for productionxx in productionx:
                if productionxx.ProductionID==ProductionID:
                    if manufactured_or_not and not productionxx.ManufacturedOrNot:
                        products=Product.query.all()
                        for product in products:
                            if product_id==str(product.ProductID):
                                product.AvailableQuantity+=manufactured_quantity
                                product.TotalQuantityProduced+=manufactured_quantity
                            if product.Type=="Milk":
                                inventory_general_items = Inventory_General.query.all()
                                for item in inventory_general_items:
                                    if item.RawMaterialName=="Sugar":
                                        if product.SugarType=="LessSugar":
                                            new_available_quantity = float(item.AvailableQuantity) - (float(manufactured_quantity) * float(0.08))
                                            item.AvailableQuantity = new_available_quantity
                                        if product.SugarType=="NormalSugar":
                                            new_available_quantity = float(item.AvailableQuantity) - (float(manufactured_quantity) * float(0.1))
                                            item.AvailableQuantity = new_available_quantity


            # Update production logic here
            production = Production.query.filter_by(ProductionID=ProductionID).first()
            production.ProductID = product_id
            production.ManufacturingDate = manufacturing_date
            production.BatchID = batch_id
            production.ManufacturedQuantity = manufactured_quantity
            production.BeansQuantity = beans_quantity
            # production.ManufacturedTime = manufactured_time
            production.ManufacturedOrNot = manufactured_or_not
            production.comments = comments

            # Commit changes to the database
            db.session.commit()

            # Redirect to production page after updating
            return redirect("/production")        

@app.route('/download_production_csv')
def download_production_csv():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        productions = Production.query.all()
        
        # Create a CSV string
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Production ID', 'Batch ID', 'Product ID', 'Manufacturing Date', 'Manufactured Quantity', 'Beans Quantity', 'Manufactured or Not', 'Comments'])
        for production in productions:
            writer.writerow([production.ProductionID, production.BatchID, production.ProductID, production.ManufacturingDate, production.ManufacturedQuantity, production.BeansQuantity, "Yes" if production.ManufacturedOrNot else "No", production.comments])

        # Set up the response headers
        output.seek(0)
        date_str = datetime.now().strftime("%d-%m-%Y")
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=productions.csv_{date_str}"}
        )



################################################################## Customers

# Routes for Customer Section
@app.route('/customers', methods=["GET", "POST"])
def customers():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Order Manager"):
        customers = Customer.query.all()
        return render_template('customers.html', customers=customers)

@app.route('/open_add_customer')
def open_add_customer():  
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Order Manager"):  
        return render_template("addCustomer.html")

#Changes
import random

def generate_customer_id(customer_name):
    # Extract initials of customer's name
    initials = ''.join(word[0].upper() for word in customer_name.split())

    # Generate random six-digit number
    random_number = '{:06d}'.format(random.randint(0, 999999))

    # Combine all parts to form the customer ID
    customer_id = f"C{initials}{random_number}"

    return customer_id

# @app.route('/add_customer', methods=["POST"])
# def add_customer():
#     if request.method == "POST":
#         # Fetch data from the form
#         customer_name = request.form['customerName']
#         address = request.form['address']
#         contact_person = request.form['contactPerson']
#         contact_number = request.form['contactNumber']
#         email_id=request.form['email']
#         customer_type = request.form['customerType']
#         gst_registered = True if request.form.get('gstRegistered') == 'on' else False
#         gst_number = request.form['gstNumber']
#         engagement_source = request.form['engagementSource']

#         # Check if the customer already exists
#         existing_customer = Customer.query.filter_by(ContactNumber=contact_number).first()

#         if existing_customer:
#             flash('error: Customer already exists!')
#             return redirect("/customers")
#         else:
#             # Generate unique customer ID
#             customer_id = generate_customer_id(customer_name)

#             new_customer = Customer(CustomerID=customer_id,
#                                     CustomerName=customer_name,
#                                     Address=address,
#                                     ContactPerson=contact_person,
#                                     ContactNumber=contact_number,
#                                     EmailId=email_id,
#                                     CustomerType=customer_type,
#                                     GSTRegistered=gst_registered,
#                                     GSTNumber=gst_number,
#                                     EngagementSource=engagement_source,
#                                     TotalCredit=0,
#                                     TotalBusinessAmount=0,
#                                     TotalTofuOrdered=0,
#                                     TotalTofuAmount=0,
#                                     TotalMilkOrdered=0,
#                                     TotalMilkAmount=0,
#                                     CrateGiven=0,
#                                     )

#             db.session.add(new_customer)
#             db.session.commit()

#             flash('success: Customer added successfully!')
#             return redirect("/customers")

import random
import string

@app.route('/add_customer', methods=["POST"])
def add_customer():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Order Manager"):
        if request.method == "POST":
            # Fetch data from the form
            customer_name = request.form['customerName']
            address = request.form['address']
            contact_person = request.form['contactPerson']
            contact_number = request.form['contactNumber']
            email_id = request.form['email']
            customer_type = request.form['customerType']
            gst_registered = True if request.form.get('gstRegistered') == 'on' else False
            gst_number = request.form['gstNumber']
            engagement_source = request.form['engagementSource']

            # Check if the customer already exists based on customer_name and contact_number
            existing_customer = Customer.query.filter_by(CustomerName=customer_name, ContactNumber=contact_number).first()

            if existing_customer:
                flash('error: Customer with the same name and contact number already exists!')
                return redirect("/customers")
            else:
                # Generate unique customer ID
                customer_id = 'C'
                customer_id += customer_name[:2].upper()
                customer_id += customer_type[:2].upper()
                customer_id += ''.join(random.choices(string.digits, k=6))  # Random 6 digits

                new_customer = Customer(CustomerID=customer_id,
                                        CustomerName=customer_name,
                                        Address=address,
                                        ContactPerson=contact_person,
                                        ContactNumber=contact_number,
                                        EmailId=email_id,
                                        CustomerType=customer_type,
                                        GSTRegistered=gst_registered,
                                        GSTNumber=gst_number,
                                        EngagementSource=engagement_source,
                                        TotalCredit=0,
                                        TotalBusinessAmount=0,
                                        TotalTofuOrdered=0,
                                        TotalTofuAmount=0,
                                        TotalMilkOrdered=0,
                                        TotalMilkAmount=0,
                                        CrateGiven=0,
                                        )

                db.session.add(new_customer)
                db.session.commit()

                flash('success: Customer added successfully!')
                return redirect("/customers")


@app.route('/delete_customer/<string:CustomerID>')
def delete_customer(CustomerID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Order Manager"):
        customer = Customer.query.filter_by(CustomerID=CustomerID).first()
        if customer:
            customer_count=Orders.query.filter_by(CustomerID=CustomerID).count()
            if customer_count > 0:
                # If referenced, prevent deletion and show a flash message
                flash("error: Cannot delete customer because it is referenced in other records.")
            else:
                # If not referenced, proceed with deletion
                db.session.delete(customer)
                db.session.commit()
                flash("success: Customer deleted successfully.")
        return redirect("/customers")

@app.route('/open_update_customer/<string:CustomerID>')
def open_update_customer(CustomerID):  
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Order Manager"):  
        customer = Customer.query.filter_by(CustomerID=CustomerID).first()
        return render_template("updateCustomer.html", customer=customer)

@app.route('/update_customer/<string:CustomerID>', methods=["POST"])
def update_customer(CustomerID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Order Manager"):
        if request.method == "POST":
            # Fetch data from the form
            customer_name = request.form['customerName']
            address = request.form['address']
            contact_person = request.form['contactPerson']
            contact_number = request.form['contactNumber']
            email_id=request.form['email']
            customer_type = request.form['customerType']
            gst_registered = True if request.form.get('gstRegistered') == 'on' else False
            gst_number = request.form['gstNumber']
            engagement_source = request.form['engagementSource']
            # first_order_date = datetime.strptime(request.form['firstOrderDate'], '%Y-%m-%d')
            # last_order_date = datetime.strptime(request.form['lastOrderDate'], '%Y-%m-%d')
            # last_bill_number = request.form['lastBillNumber']
            # last_order_id = request.form['lastOrderID']
            # total_credit = request.form['totalCredit']
            # total_business_amount = request.form['totalBusinessAmount']
            # total_tofu_ordered = request.form['totalTofuOrdered']
            # total_tofu_amount = request.form['totalTofuAmount']
            # total_milk_ordered = request.form['totalMilkOrdered']
            # total_milk_amount = request.form['totalMilkAmount']
            # status = request.form['status']
            crate_given = request.form['crateGiven']
            crate_received = request.form['crateReceived']

            # Update customer logic here
            customer = Customer.query.filter_by(CustomerID=CustomerID).first()
            customer.CustomerName = customer_name
            customer.Address = address
            customer.ContactPerson = contact_person
            customer.ContactNumber = contact_number
            customer.EmailId = email_id
            customer.CustomerType = customer_type
            customer.GSTRegistered = gst_registered
            customer.GSTNumber = gst_number
            customer.EngagementSource = engagement_source
            # customer.FirstOrderDate = first_order_date
            # customer.LastOrderDate = last_order_date
            # customer.LastBillNumber = last_bill_number
            # customer.LastOrderID = last_order_id
            # customer.TotalCredit = total_credit
            # customer.TotalBusinessAmount = total_business_amount
            # customer.TotalTofuOrdered = total_tofu_ordered
            # customer.TotalTofuAmount = total_tofu_amount
            # customer.TotalMilkOrdered = total_milk_ordered
            # customer.TotalMilkAmount = total_milk_amount
            # customer.Status = status
            customer.CrateGiven = int(crate_given) - int(crate_received)
            

            # Commit changes to the database
            db.session.commit()

            # Redirect to customers page after updating
            return redirect("/customers")

@app.route('/download_customers_csv')
def download_customers_csv():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Order Manager"):
        customers = Customer.query.all()
        
        # Create a CSV string
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Customer ID', 'Customer Name', 'Address', 'Contact Person', 'Contact Number', 'Email', 'Customer Type', 'GST Registered', 'GST Number', 'Engagement Source', 'First Order Date', 'Last Order Date', 'Last Bill Number', 'Last Order ID', 'Total Credit', 'Total Business Amount', 'Total Tofu Ordered', 'Total Tofu Amount', 'Total Milk Ordered', 'Total Milk Amount', 'Crate Given'])
        for customer in customers:
            writer.writerow([customer.CustomerID, customer.CustomerName, customer.Address, customer.ContactPerson, customer.ContactNumber, customer.EmailId, customer.CustomerType, "Yes" if customer.GSTRegistered else "No", customer.GSTNumber, customer.EngagementSource, customer.FirstOrderDate, customer.LastOrderDate, customer.LastBillNumber, customer.LastOrderID, customer.TotalCredit, customer.TotalBusinessAmount, customer.TotalTofuOrdered, customer.TotalTofuAmount, customer.TotalMilkOrdered, customer.TotalMilkAmount, customer.CrateGiven])

        # Set up the response headers
        output.seek(0)
        date_str = datetime.now().strftime("%d-%m-%Y")
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=customers.csv_{date_str}"}
        )



################################################################## Inventory

@app.route('/inventory')
def inventory(): 
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):   
        return render_template('inventory.html')

################################################################## Inventory Milk
@app.route('/inventory_milk', methods=["GET", "POST"])
def inventory_milk():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        inventory_milk_item = Inventory_Milk.query.all()
        return render_template('inventory_milk.html', inventory_milk_items=inventory_milk_item)


@app.route('/open_add_inventory_milk')
def open_add_inventory_milk():  
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):  
        return render_template("add_inventory_milk.html")
    
# @app.route('/add_milk_inventory_item', methods=["GET", "POST"])
# def add_milk_inventory_item():
#     if request.method == "POST":
#         milk_Inventory_name = request.form['milkInventoryName']
#         milk_Inventory_quantity = request.form['milkInventoryQuantity']
#         # need_to_buy = True if request.form.get('needToBuy') == 'on' else False
#         milk_Inventory_type = request.form['milkInventoryType']

#         new_milk_inventory_item = Inventory_Milk(Milk_Inventory_name=milk_Inventory_name,
#                                                  Milk_Inventory_quantity=milk_Inventory_quantity,
#                                                  Milk_Inventory_type=milk_Inventory_type
#                                                 #  Need_to_buy=need_to_buy
#                                                 )

#         db.session.add(new_milk_inventory_item)
#         db.session.commit()

#         return redirect("/inventory_milk")


import random
import string


@app.route('/add_milk_inventory_item', methods=["GET", "POST"])
def add_milk_inventory_item():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        if request.method == "POST":
            milk_Inventory_name = request.form['milkInventoryName']
            milk_Inventory_quantity = request.form['milkInventoryQuantity']
            milk_Inventory_type = request.form['milkInventoryType']

            # Generate unique Inventory_Milk_Id
            inventory_id = 'RM'
            inventory_id += milk_Inventory_name[:2].upper()
            inventory_id += milk_Inventory_quantity[:2].upper()
            inventory_id += milk_Inventory_type[:2].upper()
            inventory_id += ''.join(random.choices(string.digits, k=4))  # Random 4 digits

            # Check if item already exists based on Milk_Inventory_name
            existing_item_name = Inventory_Milk.query.filter_by(Milk_Inventory_name=milk_Inventory_name).first()

            if existing_item_name:
                flash('error: Item with the same name already exists!')
                return redirect("/inventory_milk")
            
            # Check if item already exists based on Inventory_Milk_Id
            existing_item_id = Inventory_Milk.query.filter_by(Inventory_Milk_Id=inventory_id).first()

            if existing_item_id:
                flash('error: Item with the same ID already exists!')
                return redirect("/inventory_milk")
            else:
                new_milk_inventory_item = Inventory_Milk(Inventory_Milk_Id=inventory_id,
                                                        Milk_Inventory_name=milk_Inventory_name,
                                                        Milk_Inventory_quantity=milk_Inventory_quantity,
                                                        Milk_Inventory_type=milk_Inventory_type
                                                        )

                db.session.add(new_milk_inventory_item)
                db.session.commit()

                flash('success: Milk inventory item added successfully')

                return redirect("/inventory_milk")




@app.route('/delete_inventory_milk/<string:Inventory_Milk_Id>')
def delete_inventory_milk(Inventory_Milk_Id):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        inventory_milk_item = Inventory_Milk.query.filter_by(Inventory_Milk_Id=Inventory_Milk_Id).first()
        db.session.delete(inventory_milk_item)
        db.session.commit()
        flash("success: Milk Inventory Item deleted successfully.")
        return redirect("/inventory_milk")

@app.route('/open_update_inventory_milk/<string:Inventory_Milk_Id>')
def open_update_inventory_milk(Inventory_Milk_Id):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        inventory_milk = Inventory_Milk.query.filter_by(Inventory_Milk_Id=Inventory_Milk_Id).first()
        return render_template("update_inventory_milk.html", inventory_milk=inventory_milk)

@app.route('/update_inventory_milk/<string:Inventory_Milk_Id>', methods=["GET", "POST"])
def update_inventory_milk(Inventory_Milk_Id):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        if request.method == "POST":
            # Fetch data from the form
            milk_Inventory_name = request.form['milkInventoryName']
            milk_Inventory_quantity = request.form['milkInventoryQuantity']
            milk_Inventory_type = request.form['milkInventoryType']
            need_to_buy = True if request.form.get('needToBuy') == 'on' else False

            # Update inventory milk logic here
            inventory_milk = Inventory_Milk.query.filter_by(Inventory_Milk_Id=Inventory_Milk_Id).first()
            inventory_milk.Milk_Inventory_name = milk_Inventory_name
            inventory_milk.Milk_Inventory_quantity = milk_Inventory_quantity
            inventory_milk.Need_to_buy = need_to_buy
            inventory_milk.Milk_Inventory_type=milk_Inventory_type

            # Commit changes to the database
            db.session.commit()

            # Redirect to inventory milk page after updating
            return redirect("/inventory_milk")

@app.route('/download_inventory_milk_csv')
def download_inventory_milk_csv():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        inventory_milk_items = Inventory_Milk.query.all()
        
        # Create a CSV string
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Inventory Milk ID', 'Milk Inventory Type', 'Milk Inventory Name', 'Milk Inventory Quantity'])
        for item in inventory_milk_items:
            writer.writerow([item.Inventory_Milk_Id, item.Milk_Inventory_type, item.Milk_Inventory_name, item.Milk_Inventory_quantity])

        # Set up the response headers
        output.seek(0)
        date_str = datetime.now().strftime("%d-%m-%Y")
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=inventory_milk_{date_str}.csv"}
        )

################################################################## Inventory Tofu
@app.route('/inventory_tofu', methods=["GET", "POST"])
def inventory_tofu():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        inventory_tofu_items = Inventory_Tofu.query.all()
        return render_template('inventory_tofu.html', inventory_tofu_items=inventory_tofu_items)


@app.route('/open_add_inventory_tofu')
def open_add_inventory_tofu(): 
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):   
        return render_template("add_inventory_tofu.html")
    
    
# import random
# import string

# @app.route('/add_tofu_inventory_item', methods=["GET", "POST"])
# def add_tofu_inventory_item():
#     if request.method == "POST":
#         ingredient_name = request.form['ingredientName']
#         ingredient_quantity = request.form['ingredientQuantity']

#         # Generate unique Inventory_Tofu_Id starting with 'T' followed by initials of attributes
#         tofu_id = 'T'
#         tofu_id += ''.join(word[0].upper() for word in ingredient_name.split())
#         tofu_id += ''.join(word[0].upper() for word in ingredient_quantity.split())
#         # Ensure length of Inventory_Tofu_Id is 10
#         if len(tofu_id) > 10:
#             tofu_id = tofu_id[:10]

#         # Add random characters to make the length 10 if needed
#         if len(tofu_id) < 10:
#             remaining_length = 10 - len(tofu_id)
#             tofu_id += ''.join(random.choices(string.ascii_uppercase + string.digits, k=remaining_length))

#         new_tofu_inventory_item = Inventory_Tofu(Inventory_Tofu_Id=tofu_id,
#                                                  Tofu_Inventory_name=ingredient_name,
#                                                  Tofu_Inventory_quantity=ingredient_quantity
#                                                 )

#         db.session.add(new_tofu_inventory_item)
#         db.session.commit()

#         flash('Tofu inventory item added successfully', 'success')

#         return redirect("/inventory_tofu")

import random
import string

@app.route('/add_tofu_inventory_item', methods=["GET", "POST"])
def add_tofu_inventory_item():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        if request.method == "POST":
            tofu_Inventory_name = request.form['ingredientName']
            tofu_Inventory_quantity = request.form['ingredientQuantity']
            need_to_buy = True if request.form.get('needToBuy') == 'on' else False
            # tofu_Inventory_type = request.form['tofuInventoryType']

            # Generate unique Inventory_Tofu_Id
            inventory_id = 'RT'
            inventory_id += tofu_Inventory_name[:3].upper()
            inventory_id += tofu_Inventory_quantity[:3].upper()
            inventory_id += ''.join(random.choices(string.digits, k=4))  # Random 4 digits

            # Check if item already exists based on Tofu_Inventory_name
            existing_item_name = Inventory_Tofu.query.filter_by(Tofu_Inventory_name=tofu_Inventory_name).first()

            if existing_item_name:
                flash('error: Item with the same name already exists!')
                return redirect("/inventory_tofu")
            
            # Check if item already exists based on Inventory_Tofu_Id
            existing_item_id = Inventory_Tofu.query.filter_by(Inventory_Tofu_Id=inventory_id).first()

            if existing_item_id:
                flash('error: Item with the same ID already exists!')
                return redirect("/inventory_tofu")
            else:
                new_tofu_inventory_item = Inventory_Tofu(Inventory_Tofu_Id=inventory_id,
                                                        Tofu_Inventory_name=tofu_Inventory_name,
                                                        Tofu_Inventory_quantity=tofu_Inventory_quantity
                                                        #  Need_to_buy = needtobuy
                                                        #  Tofu_Inventory_type=tofu_Inventory_type
                                                        )

                db.session.add(new_tofu_inventory_item)
                db.session.commit()

                flash('success: Tofu inventory item added successfully')

                return redirect("/inventory_tofu")




@app.route('/delete_inventory_tofu/<string:Inventory_Tofu_Id>')
def delete_inventory_tofu(Inventory_Tofu_Id):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        inventory_tofu_item = Inventory_Tofu.query.filter_by(Inventory_Tofu_Id=Inventory_Tofu_Id).first()
        db.session.delete(inventory_tofu_item)
        db.session.commit()
        flash("success: Tofu Inventory Item deleted successfully.")
        return redirect("/inventory_tofu")

@app.route('/open_update_inventory_tofu/<string:Inventory_Tofu_Id>')
def open_update_inventory_tofu(Inventory_Tofu_Id):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        inventory_tofu = Inventory_Tofu.query.filter_by(Inventory_Tofu_Id=Inventory_Tofu_Id).first()
        return render_template("update_inventory_tofu.html", inventory_tofu=inventory_tofu)

@app.route('/update_inventory_tofu/<string:Inventory_Tofu_Id>', methods=["GET", "POST"])
def update_inventory_tofu(Inventory_Tofu_Id):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        if request.method == "POST":
            # Fetch data from the form
            ingredient_name = request.form["ingredientName"]
            # essences = request.form["essences"]
            # colour = request.form["colour"]
            ingredient_quantity = request.form["ingredientQuantity"]
            # need_to_buy = True if request.form.get("needToBuy") else False

            # Update inventory tofu logic here
            inventory_tofu = Inventory_Tofu.query.filter_by(Inventory_Tofu_Id=Inventory_Tofu_Id).first()
            inventory_tofu.Tofu_Inventory_name = ingredient_name
            # inventory_tofu.Essences = essences
            # inventory_tofu.Colour = colour
            inventory_tofu.Tofu_Inventory_quantity = ingredient_quantity
            # inventory_tofu.Need_to_buy = need_to_buy

            # Commit changes to the database
            db.session.commit()

            # Redirect to inventory tofu page after updating
            return redirect("/inventory_tofu")
    
@app.route('/download_inventory_tofu_csv')
def download_inventory_tofu_csv():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        inventory_tofu_items = Inventory_Tofu.query.all()
        
        # Create a CSV string
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Inventory Tofu ID', 'Tofu Inventory Name', 'Tofu Inventory Quantity'])
        for item in inventory_tofu_items:
            writer.writerow([item.Inventory_Tofu_Id, item.Tofu_Inventory_name, item.Tofu_Inventory_quantity])

        # Set up the response headers
        output.seek(0)
        date_str = datetime.now().strftime("%d-%m-%Y")
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=inventory_tofu_{date_str}.csv"}
        )


################################################################## Inventory General
@app.route('/inventory_general', methods=["GET", "POST"])
def inventory_general():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        inventory_general_items = Inventory_General.query.all()
        return render_template('inventory_general.html', inventory_general_items=inventory_general_items)


@app.route('/open_add_inventory_general')
def open_add_inventory_general():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):    
        return render_template("add_inventory_general.html")
    

import random
import string

@app.route('/add_general_inventory_item', methods=["GET", "POST"])
def add_general_inventory_item():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        if request.method == "POST":
            raw_material_name = request.form['rawMaterialName']
            available_quantity = request.form['availableQuantity']

            # Check if item already exists based on raw_material_name
            existing_item_name = Inventory_General.query.filter_by(RawMaterialName=raw_material_name).first()

            if existing_item_name:
                flash('error: Item with the same raw material name already exists!')
                return redirect("/inventory_general")

            # Generate unique Inventory_General_ID
            general_id = 'RG'
            general_id += raw_material_name[:3].upper()
            general_id += ''.join(random.choices(string.digits, k=7))  # Random 7 digits

            new_general_inventory_item = Inventory_General(Inventory_General_ID=general_id,
                                                        RawMaterialName=raw_material_name,
                                                        AvailableQuantity=available_quantity
                                                        )

            db.session.add(new_general_inventory_item)
            db.session.commit()

            flash('success: General inventory item added successfully')

            return redirect("/inventory_general")




@app.route('/delete_inventory_general/<string:Inventory_General_ID>')
def delete_inventory_general(Inventory_General_ID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        inventory_general_item = Inventory_General.query.filter_by(Inventory_General_ID=Inventory_General_ID).first()
        db.session.delete(inventory_general_item)
        db.session.commit()
        flash("success: Inventory General Item deleted successfully.")
        return redirect("/inventory_general")

@app.route('/open_update_inventory_general/<string:Inventory_General_ID>')
def open_update_inventory_general(Inventory_General_ID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        inventory_general = Inventory_General.query.filter_by(Inventory_General_ID=Inventory_General_ID).first()
        return render_template("update_inventory_general.html", inventory_general=inventory_general)

@app.route('/update_inventory_general/<string:Inventory_General_ID>', methods=["GET", "POST"])
def update_inventory_general(Inventory_General_ID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        if request.method == "POST":
            # Fetch data from the form
            raw_material_name = request.form["rawMaterialName"]
            available_quantity = request.form["availableQuantity"]
            # need_to_buy = True if request.form.get("needToBuy") else False

            # Update inventory general logic here
            inventory_general = Inventory_General.query.filter_by(Inventory_General_ID=Inventory_General_ID).first()
            inventory_general.RawMaterialName = raw_material_name
            inventory_general.AvailableQuantity = available_quantity
            # inventory_general.Need_to_buy = need_to_buy

            # Commit changes to the database
            db.session.commit()

            # Redirect to inventory general page after updating
            return redirect("/inventory_general")
    
@app.route('/download_inventory_general_csv')
def download_inventory_general_csv():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        inventory_general_items = Inventory_General.query.all()
        
        # Create a CSV string
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Inventory General ID', 'Raw Material Name', 'Available Quantity'])
        for item in inventory_general_items:
            writer.writerow([item.Inventory_General_ID, item.RawMaterialName, item.AvailableQuantity])

        # Set up the response headers
        output.seek(0)
        date_str = datetime.now().strftime("%d-%m-%Y")
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=inventory_general_{date_str}.csv"}
        )


################################################################## Inventory Purchase
@app.route('/inventory_purchase', methods=["GET", "POST"])
def inventory_purchase():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        inventory_purchase_items = InventoryPurchase.query.all()
        vendors = RawMaterialVendor.query.all()
        return render_template('inventory_purchase.html', inventory_purchase_items=inventory_purchase_items,vendors=vendors)


@app.route('/open_add_inventory_purchase')
def open_add_inventory_purchase():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        vendors = RawMaterialVendor.query.all()    
        return render_template("add_inventory_purchase.html",vendors=vendors)
        

import random
import string

@app.route('/add_inventory_purchase_item', methods=["POST"])
def add_inventory_purchase_item():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        if request.method == "POST":
            inventory_name = request.form['inventoryName']
            vendor_id = request.form['vendorID']
            rate = request.form['rate']
            purchased_quantity = request.form['purchasedQuantity']
            purchase_date = datetime.strptime(request.form['purchaseDate'], '%Y-%m-%d')

            # Check if item already exists based on inventory_name
            existing_item_name = InventoryPurchase.query.filter_by(InventoryName=inventory_name).first()

            if existing_item_name:
                flash('error: Item with the same inventory name already exists!')
                return redirect("/inventory_purchase")
            
            # Generate unique PurchaseID
            purchase_id = 'RP'
            purchase_id += inventory_name[:3].upper()
            purchase_id += vendor_id[:2].upper()
            purchase_id += purchased_quantity[:2]
            purchase_id += ''.join(random.choices(string.digits, k=6))  # Random 6 digits

            new_inventory_purchase_item = InventoryPurchase(PurchaseID=purchase_id,
                                                            InventoryName=inventory_name,
                                                            VendorID=vendor_id,
                                                            Rate=rate,
                                                            Amount=int(purchased_quantity) * float(rate),
                                                            PurchasedQuantity=purchased_quantity,
                                                            RemainingQuantity=purchased_quantity,
                                                            PurchaseDate=purchase_date)

            db.session.add(new_inventory_purchase_item)
            db.session.commit()

            flash('success: Inventory purchase item added successfully')

            return redirect("/inventory_purchase")




@app.route('/delete_inventory_purchase/<string:PurchaseID>')
def delete_inventory_purchase(PurchaseID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        inventory_purchase_item = InventoryPurchase.query.filter_by(PurchaseID=PurchaseID).first()
        db.session.delete(inventory_purchase_item)
        db.session.commit()
        flash("success: Inventory Purchase deleted successfully.")
        return redirect("/inventory_purchase")

@app.route('/open_update_inventory_purchase/<string:PurchaseID>')
def open_update_inventory_purchase(PurchaseID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        inventory_purchase = InventoryPurchase.query.filter_by(PurchaseID=PurchaseID).first()
        vendors = RawMaterialVendor.query.all()
        return render_template("update_inventory_purchase.html", inventory_purchase=inventory_purchase,vendors=vendors)

@app.route('/update_inventory_purchase/<string:PurchaseID>', methods=["POST"])
def update_inventory_purchase(PurchaseID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        if request.method == "POST":
            # Fetch data from the form
            inventory_name = request.form['inventoryName']
            vendor_id = request.form['vendorID']
            # address = request.form['address']
            # phone_number = request.form['phoneNumber']
            rate = request.form['rate']
            purchased_quantity = request.form['purchasedQuantity']
            remaining_quantity = request.form['remainingQuantity']
            purchase_date=datetime.strptime(request.form['purchaseDate'], '%Y-%m-%d')

            # Update inventory purchase logic here
            inventory_purchase = InventoryPurchase.query.filter_by(PurchaseID=PurchaseID).first()
            inventory_purchase.InventoryName = inventory_name
            inventory_purchase.VendorID = vendor_id
            # inventory_purchase.Address = address
            # inventory_purchase.PhoneNumber = phone_number
            inventory_purchase.Rate = rate
            inventory_purchase.Amount = int(purchased_quantity)*float(rate)
            inventory_purchase.PurchasedQuantity = purchased_quantity
            inventory_purchase.RemainingQuantity = remaining_quantity
            inventory_purchase.PurchaseDate = purchase_date

            # Commit changes to the database
            db.session.commit()

            # Redirect to inventory purchase page after updating
            return redirect("/inventory_purchase")
        

@app.route('/download_inventory_purchases_csv')
def download_inventory_purchases_csv():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        inventory_purchases = InventoryPurchase.query.all()
        
        # Create a CSV string
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Purchase ID', 'Inventory Name', 'Vendor ID', 'Purchase Date', 'Rate', 'Amount', 'Purchased Quantity', 'Remaining Quantity'])
        for purchase in inventory_purchases:
            writer.writerow([purchase.PurchaseID, purchase.InventoryName, purchase.VendorID, purchase.PurchaseDate, purchase.Rate, purchase.Amount, purchase.PurchasedQuantity, purchase.RemainingQuantity])

        # Set up the response headers
        output.seek(0)
        date_str = datetime.now().strftime("%d-%m-%Y")
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=inventory_purchases_{date_str}.csv"}
        )

################################################################## DeliveryPerson

@app.route('/delivery_person', methods=["GET", "POST"])
def delivery_person():
    if session['LoggedIn']==True and (session['Designation']=="Admin"):
        delivery_people = DeliveryPerson.query.all()
        return render_template('delivery_person.html', delivery_people=delivery_people)

@app.route('/open_add_delivery_person')
def open_add_delivery_person():
    if session['LoggedIn']==True and (session['Designation']=="Admin"):
        return render_template("addDeliveryPerson.html")


import random
import string

@app.route('/add_delivery_person', methods=["POST"])
def add_delivery_person():
    if session['LoggedIn']==True and (session['Designation']=="Admin"):
        if request.method == "POST":
            delivery_person_name = request.form['deliveryPersonName']
            contact_number = request.form['contactNumber']
            username=request.form['username']
            password=request.form['password']
            # total_deliveries = request.form['totalDeliveries']
            active_or_obsolete = True if request.form.get('activeOrObsolete') == 'on' else False
            preferred_delivery_locations = request.form['preferredDeliveryLocations']

            # Check if the delivery person already exists based on delivery_person_name and contact_number
            existing_delivery_person = DeliveryPerson.query.filter_by(DeliveryPersonName=delivery_person_name, ContactNumber=contact_number).first()

            if existing_delivery_person:
                flash('error: Delivery person with the same name and contact number already exists!')
                return redirect("/delivery_person")
            else:
                # Generate unique delivery person ID
                delivery_person_id = 'DP'
                delivery_person_id += delivery_person_name[:2].upper()
                delivery_person_id += preferred_delivery_locations[:2].upper()
                delivery_person_id += ''.join(random.choices(string.digits, k=6))  # Random 6 digits

            new_delivery_person = DeliveryPerson(DeliveryPersonID=delivery_person_id,
                                                DeliveryPersonName=delivery_person_name,
                                                ContactNumber=contact_number,
                                                TotalDeliveries=0,
                                                ActiveOrObsolete=active_or_obsolete,
                                                PreferredDeliveryLocations=preferred_delivery_locations)

            db.session.add(new_delivery_person)
            db.session.commit()
            curr_User=DeliveryPerson.query.filter_by(ContactNumber=contact_number).first()

            new_User=Users(User_ID=curr_User.DeliveryPersonID,User_fullname=curr_User.DeliveryPersonName,User_phone=curr_User.ContactNumber ,User_password=password,UserName=username,User_Designation="Delivery Person")
            db.session.add(new_User)
            db.session.commit()

            flash('success: Delivery person added successfully!')
            return redirect("/delivery_person")


@app.route('/delete_delivery_person/<string:DeliveryPersonID>')
def delete_delivery_person(DeliveryPersonID):
    if session['LoggedIn']==True and (session['Designation']=="Admin"):
        delivery_person = DeliveryPerson.query.filter_by(DeliveryPersonID=DeliveryPersonID).first()
        if delivery_person:
            delivery_person_count=Orders.query.filter_by(DeliveryPersonID=DeliveryPersonID).count()
            if delivery_person_count > 0:
                # If referenced, prevent deletion and show a flash message
                flash("error: Cannot delete delivery person because it is referenced in other records.")
            else:
                # If not referenced, proceed with deletion
                db.session.delete(delivery_person)
                db.session.commit()
                flash("success: Delivery person deleted successfully.")    
        return redirect("/delivery_person")

@app.route('/open_update_delivery_person/<string:DeliveryPersonID>')
def open_update_delivery_person(DeliveryPersonID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" ):
        delivery_person = DeliveryPerson.query.get_or_404(DeliveryPersonID)
        return render_template("updateDeliveryPerson.html", delivery_person=delivery_person)

@app.route('/update_delivery_person/<string:DeliveryPersonID>', methods=["POST"])
def update_delivery_person(DeliveryPersonID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" ):
        if request.method == "POST":
            delivery_person_name = request.form["deliveryPersonName"]
            contact_number = request.form["contactNumber"]
            # total_deliveries = request.form["totalDeliveries"]
            active_or_obsolete = True if request.form.get("activeOrObsolete") else False
            preferred_delivery_locations = request.form["preferredDeliveryLocations"]

            delivery_person = DeliveryPerson.query.get_or_404(DeliveryPersonID)
            delivery_person.DeliveryPersonName = delivery_person_name
            delivery_person.ContactNumber = contact_number
            # delivery_person.TotalDeliveries = total_deliveries
            delivery_person.ActiveOrObsolete = active_or_obsolete
            delivery_person.PreferredDeliveryLocations = preferred_delivery_locations

            db.session.commit()

            return redirect("/delivery_person")

@app.route('/assign_delivery/<delivery_person_id>', methods=['POST'])
def assign_delivery(delivery_person_id):
    if session['LoggedIn']==True and (session['Designation']=="Admin" ):
        if request.method == 'POST':
            # Get the data from the form or request body
            order_id = request.form['order_id']  # Assuming you have an 'order_id' field in your form

            # Perform any necessary operations with the delivery person ID and order ID
            # For example, you might want to update the order record in the database
            # with the assigned delivery person ID.

            # Here, I'm just printing the assigned delivery person ID and order ID for demonstration purposes
            print(f"Assigned delivery person ID {delivery_person_id} to order ID {order_id}")

            # Redirect the user to a relevant page after assigning the delivery
            return redirect("/orders")  # Redirect to the orders page
        else:
            # Handle other HTTP methods if needed
            return "Method Not Allowed", 405 
        
@app.route('/download_delivery_persons_csv')
def download_delivery_persons_csv():
    if session['LoggedIn']==True and (session['Designation']=="Admin"):
        delivery_persons = DeliveryPerson.query.all()
        
        # Create a CSV string
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Delivery Person ID', 'Delivery Person Name', 'Contact Number', 'Total Deliveries', 'Preferred Delivery Locations', 'Active or Obsolete'])
        for delivery_person in delivery_persons:
            writer.writerow([delivery_person.DeliveryPersonID, delivery_person.DeliveryPersonName, delivery_person.ContactNumber, delivery_person.TotalDeliveries, delivery_person.PreferredDeliveryLocations, "Active" if delivery_person.ActiveOrObsolete else "Obsolete"])

        # Set up the response headers
        output.seek(0)
        date_str = datetime.now().strftime("%d-%m-%Y")
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=delivery_persons_{date_str}.csv"}
        )

################################################################## Sticker
@app.route('/sticker', methods=["GET", "POST"])
def sticker():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        sticker_items = Sticker.query.all()
        return render_template('sticker.html', sticker_items=sticker_items)


@app.route('/open_add_sticker')
def open_add_sticker():   
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"): 
        return render_template("add_sticker.html")
    

import random
import string

@app.route('/add_sticker_item', methods=["GET", "POST"])
def add_sticker_item():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        if request.method == "POST":
            sticker_type = request.form['stickerType']
            flavour_name = request.form['flavourName']
            sugar_type = request.form['sugarType']
            available_quantity = request.form['availableQuantity']

            # Check if item already exists based on both Flavour_name and SugarType
            existing_item = Sticker.query.filter_by(Flavour_name=flavour_name, SugarType=sugar_type).first()

            if existing_item:
                flash('error: Item already exists!')
                return redirect("/sticker")
            
            # Generate unique StickerID
            sticker_id = 'RS'
            sticker_id += sticker_type[:2].upper()
            sticker_id += flavour_name[:2].upper()
            sticker_id += sugar_type[:2].upper()
            sticker_id += ''.join(random.choices(string.digits, k=5))  # Random 5 digits

            new_sticker_item = Sticker(StickerID=sticker_id,
                                        Type=sticker_type,
                                        Flavour_name=flavour_name,
                                        SugarType=sugar_type,
                                        AvailableQuantity=available_quantity)

            db.session.add(new_sticker_item)
            db.session.commit()

            flash('success: Sticker item added successfully')

            return redirect("/sticker")



@app.route('/delete_sticker/<string:StickerID>')
def delete_sticker(StickerID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        sticker_item = Sticker.query.filter_by(StickerID=StickerID).first()
        db.session.delete(sticker_item)
        db.session.commit()
        flash("success: Sticker Item deleted successfully.")
        return redirect("/sticker")

@app.route('/open_update_sticker/<string:StickerID>')
def open_update_sticker(StickerID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        sticker = Sticker.query.filter_by(StickerID=StickerID).first()
        return render_template("update_sticker.html", sticker=sticker)

@app.route('/update_sticker/<string:StickerID>', methods=["GET", "POST"])
def update_sticker(StickerID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        if request.method == "POST":
            # Fetch data from the form
            sticker_type = request.form["stickerType"]
            flavour_name = request.form["flavourName"]
            sugar_type = request.form["sugarType"]
            available_quantity = request.form["availableQuantity"]

            # Update sticker logic here
            sticker = Sticker.query.filter_by(StickerID=StickerID).first()
            sticker.Type = sticker_type
            sticker.Flavour_name = flavour_name
            sticker.SugarType = sugar_type
            sticker.AvailableQuantity = available_quantity

            # Commit changes to the database
            db.session.commit()

            # Redirect to sticker page after updating
            return redirect("/sticker")

@app.route('/download_stickers_csv')
def download_stickers_csv():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        stickers = Sticker.query.all()
        
        # Create a CSV string
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Sticker ID', 'Type', 'Flavour Name', 'Sugar Type', 'Available Quantity'])
        for sticker in stickers:
            writer.writerow([sticker.StickerID, sticker.Type, sticker.Flavour_name, sticker.SugarType, sticker.AvailableQuantity])

        # Set up the response headers
        output.seek(0)
        date_str = datetime.now().strftime("%d-%m-%Y")
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=stickers_{date_str}.csv"}
        )

################################################################## Raw Material Vendor

@app.route('/raw_material_vendor', methods=["GET", "POST"])
def raw_material_vendor():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        vendors = RawMaterialVendor.query.all()
        return render_template('raw_material_vendor.html', vendors=vendors)

@app.route('/open_add_raw_material_vendor')
def open_add_raw_material_vendor():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        return render_template("add_raw_material_vendor.html")


import random
import string

@app.route('/add_raw_material_vendor', methods=["POST"])
def add_raw_material_vendor():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        if request.method == "POST":
            vendor_name = request.form['vendorName']
            vendor_address = request.form['vendorAddress']
            vendor_phone_number = request.form['vendorPhoneNumber']

            # Check if vendor already exists based on vendor_name and vendor_phone_number
            existing_vendor = RawMaterialVendor.query.filter_by(VendorName=vendor_name, VendorPhoneNumber=vendor_phone_number).first()

            if existing_vendor:
                flash('error: Vendor with the same name and phone number already exists!')
                return redirect("/raw_material_vendor")
            
            # Generate unique VendorID
            vendor_id = 'RV'
            vendor_id += vendor_name[:2].upper()
            vendor_id += vendor_address[:2].upper()
            vendor_id += vendor_phone_number[:2]
            vendor_id += ''.join(random.choices(string.digits, k=6))  # Random 6 digits

            new_vendor = RawMaterialVendor(VendorID=vendor_id,
                                        VendorName=vendor_name,
                                        VendorAddress=vendor_address,
                                        VendorPhoneNumber=vendor_phone_number)

            db.session.add(new_vendor)
            db.session.commit()

            flash('success: Raw material vendor added successfully')

            return redirect("/raw_material_vendor")


@app.route('/delete_raw_material_vendor/<string:VendorID>')
def delete_raw_material_vendor(VendorID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        vendor = RawMaterialVendor.query.get(VendorID)
        if vendor:
            vendor_count=1 if InventoryPurchase.query.filter_by(VendorID=VendorID).first() else 0
            if vendor_count > 0:
                # If referenced, prevent deletion and show a flash message
                flash("error: Cannot delete vendor because it is referenced in other records.")
            else:
                # If not referenced, proceed with deletion
                db.session.delete(vendor)
                db.session.commit()
                flash("success: Vendor deleted successfully.")
        return redirect("/raw_material_vendor")

@app.route('/open_update_raw_material_vendor/<string:VendorID>')
def open_update_raw_material_vendor(VendorID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        vendor = RawMaterialVendor.query.get(VendorID)
        return render_template("update_raw_material_vendor.html", vendor=vendor)

@app.route('/update_raw_material_vendor/<string:VendorID>', methods=["POST"])
def update_raw_material_vendor(VendorID):
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        if request.method == "POST":
            vendor_name = request.form['vendorName']
            vendor_address = request.form['vendorAddress']
            vendor_phone_number = request.form['vendorPhoneNumber']

            vendor = RawMaterialVendor.query.get(VendorID)
            vendor.VendorName = vendor_name
            vendor.VendorAddress = vendor_address
            vendor.VendorPhoneNumber = vendor_phone_number

            db.session.commit()

            return redirect("/raw_material_vendor")
    
@app.route('/download_raw_material_vendors_csv')
def download_raw_material_vendors_csv():
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Production Manager"):
        raw_material_vendors = RawMaterialVendor.query.all()
        
        # Create a CSV string
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Vendor ID', 'Vendor Name', 'Vendor Phone Number', 'Vendor Address'])
        for vendor in raw_material_vendors:
            writer.writerow([vendor.VendorID, vendor.VendorName, vendor.VendorPhoneNumber, vendor.VendorAddress])

        # Set up the response headers
        output.seek(0)
        date_str = datetime.now().strftime("%d-%m-%Y")
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=raw_material_vendors_{date_str}.csv"}
        )
    
###################################################################################### Delivery person interface    
@app.route('/deliveryInterface')
def deliveryInterface():
    if session['LoggedIn']==True and session['Designation']=="Delivery Person":
        print(session['id'])
        customers=Customer.query.all()
        products=Product.query.all()
        orders=Orders.query.filter_by(DeliveryPersonID=session['id'], DeliveredOrNot=False).all()

        return render_template('deliveryPersonInterface.html',orders=orders,customers=customers,products=products)
    
@app.route('/openDeliveryPersonInterfaceUpdate/<string:OrderID>')
def openDeliveryPersonInterfaceUpdate(OrderID):  
    if session['LoggedIn']==True and (session['Designation']=="Admin" or  session['Designation']=="Delivery Person"):  
        order = Orders.query.filter_by(OrderID=OrderID).first()
        products=Product.query.all()
        customers=Customer.query.all()
        delivery_people = DeliveryPerson.query.all()
        return render_template("deliveryPersonInterfaceUpdate.html", order=order,products=products,customers=customers,delivery_people=delivery_people)
  
    
    

@app.route('/updateDeliveryPersonInterfaceUpdate/<string:order_id>', methods=['GET', 'POST'])
def updateDeliveryPersonInterfaceUpdate(order_id):
    if session['LoggedIn']==True and session['Designation']=="Delivery Person":
    # Retrieve the order from the database based on the order_id
        order = Orders.query.filter_by(OrderID=order_id).first()

        if request.method == 'POST':
            batch_id = request.form['batchID'] or None
            payment_type = request.form['paymentType']
            customer_id = request.form['customerID']  
            product_id = request.form['productID']
            quantity = int(request.form['quantity'])
            delivery_person_id = request.form['deliveryPersonID'] if request.form['deliveryPersonID'] else None
            payment_received = True if request.form.get('paymentReceivedOrNot') == 'on' else False
            crates_given = int(request.form['cratesGiven']) if request.form['cratesGiven'] else 0
            delivered = True if request.form.get('deliveredOrNot') == 'on' else False
            actual_order_delivered_date = datetime.strptime(request.form['actualOrderDeliveredDate'], '%Y-%m-%d')
            amount = float(request.form['Amount']) if request.form['Amount'] else None
           
            products=Product.query.all()
            orderx = Orders.query.all() 
            for orderxx in orderx:
                if orderxx.OrderID==order_id:     
                    if delivered and not orderxx.DeliveredOrNot :
                        customers = Customer.query.all()
                        for product in products:
                            if product_id==str(product.ProductID):
                                product.AvailableQuantity-=quantity
                                for customer in customers:
                                    if customer_id==str(customer.CustomerID):
                                        customer.TotalCredit+=int(quantity)
                                        customer.CrateGiven+=crates_given
                                        customer.TotalBusinessAmount+=float(str(amount))
                                        if product.Type=='Tofu':
                                            customer.TotalTofuAmount+=float(str(amount))
                                            customer.TotalTofuOrdered+=quantity
                                        if product.Type=='Milk':
                                            customer.TotalMilkAmount+=float(str(amount))
                                            customer.TotalMilkOrdered+=quantity

                        delivery_people = DeliveryPerson.query.all()    
                        for people in delivery_people:
                            if delivery_person_id==str(people.DeliveryPersonID):
                                people.TotalDeliveries+=1  

            order = Orders.query.filter_by(OrderID=order_id).first()
            order.BatchID = batch_id
            order.PaymentType = payment_type
            order.PaymentReceivedOrNot = payment_received
            order.CratesGiven = crates_given
            order.DeliveredOrNot = delivered
            order.ActualOrderDeliveredDate = actual_order_delivered_date
            

            # Commit the changes to the database
            db.session.commit()

            # Redirect to the orders page or any other appropriate page
            return redirect('/deliveryInterface')

       

######################################################################## employeees
@app.route('/employee')
def employee():
    if session['LoggedIn']==True and session['Designation']=="Admin":
        users=Users.query.all()
        return render_template('employee.html',users=users)

# @app.route('/add_employee',methods=['GET', 'POST'])
# def sdd_employee():
#     if session['LoggedIn']==True and session['Designation']=="Admin":
#         if  request.method =='POST':
#             name=request.form['PersonName']
#             email=request.form['email']
#             password=request.form['password']
#             phone=request.form['contactNumber']
#             address=request.form['Address']
#             userDesignation=request.form['userDesignation']
#             username=request.form['username']
#             newUser=Users(User_fullname=name, User_Address=address, User_phone=phone, User_email=email, User_password=password, UserName=username, User_Designation=userDesignation)
#             db.session.add(newUser)
#             db.session.commit()
#             return redirect('employee')

#         return render_template('addemployee.html')

@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if session['LoggedIn'] == True and session['Designation'] == "Admin":
        if request.method == 'POST':
            name = request.form['PersonName']
            email = request.form['email']
            password = request.form['password']
            phone = request.form['contactNumber']
            address = request.form['Address']
            user_designation = request.form['userDesignation']
            username = request.form['username']
            
            # Check if the username or email already exists
            existing_user = Users.query.filter(
                (Users.UserName == username) | (Users.User_phone == phone)
            ).first()
            
            if existing_user:
                flash('error: Username or Phone Number already exists!')
                return redirect('/employee')

            # Generate employee ID
            employee_id = generate_employee_id(name)

            # Create a new user object
            new_user = Users(User_fullname=name, User_Address=address, User_phone=phone,
                             User_email=email, User_password=password, UserName=username,
                             User_Designation=user_designation, User_ID=employee_id)
            
            # Add the new user to the database
            db.session.add(new_user)
            db.session.commit()
            
            flash('success: Employee added successfully!')
            return redirect('employee')

        return render_template('addemployee.html')


def generate_employee_id(name):
    # Extract initials from the name
    initials = name[:3].upper()
    
    # Generate a random three-digit number
    random_number = '{:03d}'.format(random.randint(0, 999))
    
    # Combine initials and random number to form employee ID
    employee_id = f"EID{initials}{random_number}"
    
    return employee_id

    

@app.route('/update_user/<string:userName>', methods=['GET', 'POST'])
def update_user(userName):
    user = Users.query.get_or_404(userName)
    if request.method == 'POST':
        # Update user information based on form data
        user.User_fullname = request.form['fullname']
        user.User_Address = request.form['address']
        user.User_email = request.form['email']
        user.User_phone = request.form['phone']
        user.User_Designation = request.form['userDesignation']
        user.UserName = request.form['username']
        user.User_password = request.form['password']
        
        # Commit changes to the database
        db.session.commit()
        return redirect(url_for('employee'))
    return render_template('update_user.html', user=user)


@app.route('/delete_user/<string:userName>', methods=['GET', 'POST'])
def delete_user(userName):
    user = Users.query.get_or_404(userName)
    db.session.delete(user)
    db.session.commit()
    flash("success: Employee deleted successfully.")
    return redirect(url_for('employee'))


@app.route('/download_employee_details_csv')
def download_employee_details_csv():
    if session['LoggedIn'] and (session['Designation'] == "Admin"):
        # Query all employees from the database
        employees = Users.query.all()

        # Create a CSV string
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['User ID', 'Full Name', 'Address', 'Phone', 'Email', 'Designation'])
        for employee in employees:
            writer.writerow([employee.User_ID, employee.User_fullname, employee.User_Address, 
                              employee.User_phone, employee.User_email, employee.User_Designation])

        # Set up the response headers
        output.seek(0)
        date_str = datetime.now().strftime("%d-%m-%Y")
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=employee_details_{date_str}.csv"}
        )
    else:
        # Handle unauthorized access
        return "Unauthorized", 401

#########################################################################################


@dash_app.callback([Output('customer-type-plot', 'figure'),
                   Output('engagement-source-plot', 'figure'),
                   Output('credit-distribution-plot', 'figure'),
                   Output('business-amount-plot', 'figure'),
                   Output('product-type-plot', 'figure'),
                   Output('product-price-plot', 'figure'),
                   Output('manufactured-quantity-plot', 'figure'),
                   Output('order-quantity-amount-plot', 'figure'),
                   Output('order-type-plot', 'figure'),
                   Output('delivery-status-plot', 'figure'),
                   Output('kpi-summary', 'children')],
                   [Input('url', 'pathname')])
def update_plots(pathname):
    # Convert sample data to DataFrame
    customer_df = table_to_dataframe(Customer)
    product_df = table_to_dataframe(Product)
    order_df = table_to_dataframe(Orders)

    # Customer Distribution by Type (Bar Plot)
    customer_type_plot = px.bar(customer_df, x='CustomerType', title="Customer Distribution by Type",
                                labels={'CustomerType': 'Customer Type', 'count': 'Count'})

    # Customer Engagement Source (Pie Chart)
    engagement_source_plot = px.pie(customer_df, names='EngagementSource', title='Customer Engagement Source')

    # Customer Credit Distribution (Histogram)
    credit_distribution_plot = px.histogram(customer_df, x='TotalCredit', title='Customer Credit Distribution')

    # Total Business Amount over Time (Line Plot)
    business_amount_plot = px.line(customer_df, x='CustomerID', y='TotalCredit', title='Total Business Amount over Time')

    # Product Type Distribution (Pie Chart)
    product_type_plot = px.pie(product_df, names='ProductName', title='Product Type Distribution')

    # Product Price Distribution (Histogram)
    product_price_plot = px.histogram(product_df, x='Price', title='Product Price Distribution')

    # Manufactured Quantity Distribution (Histogram)
    manufactured_quantity_plot = px.histogram(product_df, x='TotalQuantityProduced', title='Manufactured Quantity Distribution')

    # Order Quantity vs. Order Amount (Scatter Plot)
    order_quantity_amount_plot = px.scatter(order_df, x='Quantity', y='Amount', title='Order Quantity vs. Order Amount')

    # Order Type Distribution (Pie Chart)
    order_type_plot = px.pie(order_df, names='PaymentType', title='Order Type Distribution')

    # Delivery Status Distribution (Pie Chart)
    delivery_status_plot = px.pie(order_df, names='DeliveredOrNot', title='Delivery Status Distribution')

    total_customers = len(customer_df)
    total_products = len(product_df)
    total_orders = len(order_df)
    total_business_amount,total_products = calculate_revenue_and_pending_amount(order_df)
    total_business_amount_1mo,total_Pending_amount_1mo=calculate_revenue_and_pending_amount_one_month(order_df)
    kpi_summary = html.Div([
    html.Div([
        html.Div([
            html.H4('Total Customers'),
            html.P(total_customers)
        ], className='kpi-item'),
        html.Div([
            html.H4('Total Pending amount(1 year)'),
            html.P(total_products)
        ], className='kpi-item'),
        html.Div([
            html.H4('Total Orders(Till Date)'),
            html.P(total_orders)
        ], className='kpi-item'),
        html.Div([
            html.H4('Total Business Amount (1 Year)'),
            html.P(total_business_amount)
        ], className='kpi-item'),
        html.Div([
            html.H4('Total Customers gained(1 Month)'),
            html.P(total_business_amount)
        ], className='kpi-item'),
        html.Div([
            html.H4('Total Orders (1 Month)'),
            html.P(total_business_amount)
        ], className='kpi-item'),
        html.Div([
            html.H4('Total Pending Amount (1 Month)'),
            html.P(total_Pending_amount_1mo)
        ], className='kpi-item'),
        html.Div([
            html.H4('Total Business Amount (1 Month)'),
            html.P(total_business_amount_1mo)
        ], className='kpi-item')
    ], className='kpi-container')
], className='card')

    return (customer_type_plot, engagement_source_plot, credit_distribution_plot, business_amount_plot,
            product_type_plot, product_price_plot, manufactured_quantity_plot, order_quantity_amount_plot,
            order_type_plot, delivery_status_plot,kpi_summary)

# Define layout of the Plotly Dash app
dash_app.layout = html.Div([
    html.Div(className="navbar", children=[
        html.Div(className="navbar-left", children="AVA SOY Nutrients"),
        html.Div(className="navbar-center", children=[
            html.A(href="/orders", children=[html.I(className="fa-solid fa-cart-shopping"), " Orders"]),
            html.A(href="/inventory", children=[html.I(className="fa-solid fa-cubes"), " Raw Material"]),
            html.A(href="/production", children=[html.I(className="fa-solid fa-gears fa-lg"), " Production"]),
            html.A(href="/product", children=[html.I(className="fa-solid fa-boxes-stacked"), " Product"]),
            html.A(href="/variousinsights", children=[html.I(className="fa-solid fa-chart-line"), " Various Insights"]),
            html.A(href="/customers", children=[html.I(className="fa-solid fa-users"), " Customers"]),
            html.A(href="/delivery_person", children=[html.I(className="fa-solid fa-people-carry-box"), " Delivery Person"]),
            html.A(href="/employee", children=[html.I(className="fa-solid fa-users-gear"), " Employee"])
        ])
    ]),
    html.Div(id='kpi-summary') ,
    dcc.Location(id='url', refresh=False),
    html.H1(children='Customer Insights'),
    html.Div([
        html.Div([
            dcc.Graph(id='customer-type-plot'),
            dcc.Graph(id='engagement-source-plot')
        ], style={'display': 'inline-block', 'width': '49%'}),
        html.Div([
            dcc.Graph(id='credit-distribution-plot'),
            dcc.Graph(id='business-amount-plot')
        ], style={'display': 'inline-block', 'width': '49%'})
    ]),
    html.H1(children='Product Insights'),
    html.Div([
        html.Div([
            dcc.Graph(id='product-type-plot'),
            dcc.Graph(id='product-price-plot')
        ], style={'display': 'inline-block', 'width': '49%'}),
        html.Div([
            dcc.Graph(id='manufactured-quantity-plot')
        ], style={'display': 'inline-block', 'width': '49%'})
    ]),
    html.H1(children='Order Insights'),
    html.Div([
        html.Div([
            dcc.Graph(id='order-quantity-amount-plot'),
            dcc.Graph(id='order-type-plot')
        ], style={'display': 'inline-block', 'width': '49%'}),
        html.Div([
            dcc.Graph(id='delivery-status-plot')
        ], style={'display': 'inline-block', 'width': '49%'})
    ])
])



@app.route('/variousinsights/')
def render_dashboard():
    if session['LoggedIn'] and (session['Designation'] == "Admin"):
        return dash_app.index()
    else:
        return "You are Not authorized"






if __name__ == '__main__':
    app.run(debug=True)

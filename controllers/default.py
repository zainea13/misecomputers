# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

# ---- example index page ----
from gluon import *
from gluon.tools import XML
import datetime
from datetime import date, datetime, timedelta
import json
from gluon.storage import Storage
from gluon.contrib.stripe import Stripe
import stripe
import random
import math

from private.private import *

stripe.api_key = stripe_api_keys['sk']
STRIPE_PUBLISHABLE_KEY = stripe_api_keys['pk']


# Menu Stuff
response.menu = [
    (T('Home'), False, URL('default', 'index'), [])
]

for category in db(db.categories).select():
    cat_id = category['id']
    cat_name = category['category_name']
    cat_link = cat_name.replace(" ", "-")
    response.menu.append(
        (T(cat_name), False,URL('default/category_page', (str(cat_id) + '--' + cat_link)), [])
    )


def clear_ram_cache():
    cache.ram.clear() # Clears all items from the RAM cache
    response.flash = "RAM cache cleared!"
    redirect(URL('index')) # Redirect to a main page


def calculate_shipping(items):
    # Get standard shipping rate
    rate = int(db(db.config).select().first().shipping_rate)
    # caclulate shipping
    return rate + rate * 1.4 * math.log(items)
    

# NOT FINISHED, this function is a work in progress
def shopping_cart_count():
    session_id = response.session_id
    user_id = auth.user_id

    # here we get the results from the database table, based on if the user is logged in or not
    where_stmt = ""
    if auth.user:
        where_stmt = f"sc.user_id = {str(auth.user.id)}"
    else:
        where_stmt = f"sc.session_id = '{str(response.session_id)}'"

    # here we fetch it, and then start adding up items
    query = "SELECT sc.* FROM shopping_cart2 AS sc WHERE " + where_stmt
    cart_items = db.executesql(query, as_dict=True)

    total_items = 0
    for item in cart_items:
        total_items += int(item['quantity'])
    
    session.cart_counter = total_items

    return total_items

shopping_cart_count()


def shopping_cart_subtotal():
    session_id = response.session_id
    user_id = auth.user_id

    # here we get the results from the database table, based on if the user is logged in or not
    where_stmt = ""
    if auth.user:
        where_stmt = f"sc.user_id = {str(auth.user.id)}"
    else:
        where_stmt = f"sc.session_id = '{str(response.session_id)}'"

    # here we fetch it, and then start adding up items
    query = "SELECT sc.* FROM shopping_cart2 AS sc WHERE " + where_stmt
    cart_items = db.executesql(query, as_dict=True)

    cart_subtotal = 0
    for item in cart_items:
        product_id = item['product_id']
        product = db(db.products.id == product_id).select().first()
        cart_subtotal += (float(product['price']) * int(item['quantity']))
    
    session.cart_subtotal = cart_subtotal

    return cart_subtotal



# ---- define pages ----

def index():
    response.title='MISE Computer Store'
    session.forced = True
    categories = db(db.categories).select()

    return dict(message=T('Welcome to web2py!'), categories=categories)

def privacy():
    response.title='MISE - Privacy Policy'
    return locals()

def terms():
    response.title='MISE - Terms'
    return locals()

def aboutus():
    response.title='MISE - About Us'
    return locals()

def contact():
    response.title='MISE - Contact'
    form = SQLFORM.factory(
        Field('name',
              requires=IS_NOT_EMPTY()),
        Field('email',
              requires=IS_EMAIL()),
        Field('message',
              'text',
              requires=IS_NOT_EMPTY())
    )

    if form.process().accepted:
        mail.send(
            to=f'misecomputers@gmail.com',
            subject=f'Website Contact from {form.vars.name}',
            reply_to=form.vars.email,
            message=form.vars.message
        )
        mail.send(
            to=form.vars.email,
            subject=f'Your copy of your Contact email with Mise Computers',
            message=f'<html lang="en"><head></head><body>You sent us this message: <p> {form.vars.message} </p> We will be in touch soon!</body></html>'
        )
        session.flash = "Email sent!"
        redirect(URL('index'))      

    return locals()

def search():
    results = None
    #if form.process().accepted:
    keyword = request.vars.keyword
    print(keyword)
    if keyword:
        results = db((db.products.product_name.contains(keyword))).select()
    
    response.title=f'MISE - Search results for "{keyword}"'

    # Print all fields to see what's available
    print("Products fields:", [field for field in db.products])
    print("Categories fields:", [field for field in db.categories])

    return dict(locals(), results=results)

def product_entry_form():
    response.title=f'MISE - Product Entry Form'
    attributes = db(db.attribute_description).select()
    categories = db(db.categories).select()
    brands = db(db.brand).select()
    attr = {}
    img_paths = {}
    img_alts = {}

    for key, value in request.vars.items():
        if "attr" in key:
            attr[key] = value
        if "img-path" in key:
            img_paths[key] = value
        if "img-alt" in key:
            img_alts[key] = value

    r = request.vars


    if request.env.request_method == 'POST':
        product_id = db.products.insert(
            product_name=r.product_name, 
            stock_qty=r.stock_qty, 
            price=r.price, 
            category_id=r.category,
            description=r.description,
            brand_id=r.brand
            )
        
        for i in range(len(img_paths)):
            main = False
            if i == 0:
                main = True
            else:
                main = False

            db.product_images.insert(
                product_id=product_id,
                image_filename=img_paths[f"img-path-{i}"],
                image_alt=img_alts[f"img-alt-{i}"],
                main_image=main
            )

        for attr_name, attr_value in attr.items():
            db.product_attribute.insert(
                attribute_id=attr_name.strip("attr-"),
                attribute_value=attr_value,
                product_id=product_id,
                is_key_feature=True
            )

        product = db.products(product_id)
    else:
        product = None

    return locals()


def item_page():
    
    item = request.args(0).split("--") # value: 2--Test-Laptop-Product-2
    product_id = item[0] # 2 
    product = db.products[product_id] # returns rows for that product id
    cat = (db(db.categories.id == product.category_id).select().first().category_name).lower()
    cat = cat.replace("&","").replace(" ","_")
    brand = (db(db.brand.id == product.brand_id).select().first()).brand_name.lower()
    images = db(db.product_images.product_id == product_id).select() # grabs images that match product id

    stock_qty = product.stock_qty
    
    # test = session.my_test
    session_id = response.session_id
    response.title=f'MISE - {product['product_name']}'
    return locals()


def category_page():
    link_arg = request.args(0).split("--")
    cat_id = link_arg[0]
    cat_id_fix = link_arg[0]
    cat_name_fix = ""

    for row in db(db.categories).select():
        if row['id'] == int(cat_id):
            cat_name_fix = row['category_name'].title() 
        else:
            pass
    
    options = get_filter_dict(cat_id) # filter options based on category and products
    filter_dict = get_selected_filters(options) # filters selected by user
    order = request.vars.ORDER or '' # sort value
    products = filtered_products(cat_id, filter_dict, order) # products based on user's criteria
    is_filter = db((db.category_attribute.category_id == cat_id) & (db.category_attribute.isFilter == True)).select()

    response.title=f'MISE - All {cat_name_fix}'
    return locals()

# retrieves products from database that are within the specified category, with an optional order by clause
def get_products(cat_id, order=''):

    sqlstmt = "SELECT p.*, pi.image_filename, pi.product_id, pi.image_alt, pi.main_image FROM products AS p INNER JOIN product_images AS pi ON p.id = pi.product_id WHERE pi.main_image = 'T' AND p.category_id = " + cat_id + order 
    for row in db(db.categories).select():
        if row['id'] == int(cat_id):
            cat_name_fix = row['category_name'].capitalize() 
        else:
            pass
    products = db.executesql(sqlstmt, as_dict=True)
    return products


def filtered_products(cat_id, filter_dict, order):
    '''
        Filters products based on user selections
        Args:   cat_id: category_id
                filter_dict: dictionary containing user selections
                order: an optional sort selection
        Returns: a list of products
    '''
    # retrieves all products from the db in that category
    product_list = get_products(cat_id, get_order_string(order))
    results = []

    if 'Price' in filter_dict:
        price_range = filter_dict['Price'][0]
        min_price, max_price = map(float, price_range.split("--"))
        del filter_dict['Price'] # removes Price from filter_dict so as not to affect later logic

        product_list = [product for product in product_list if min_price <= product['price'] <= max_price] # only adds a product_id if it fits within selected range

    if not filter_dict:
        return product_list # if there aren't any more filters, return the list of products

    for attribute, values in filter_dict.items():
        # queries the product_attribute table for each selected option and adds the list to results
        if values:
            attr_row = db(db.attribute_description.attribute_name == attribute).select().first()
            if not attr_row:
                continue
            rows = db((db.product_attribute.attribute_id == attr_row.id) & (db.product_attribute.attribute_value.belongs(values))).select(db.product_attribute.product_id)
            product_ids = set([row.product_id for row in rows])
            results.append(product_ids)

    # creates a set of product_ids that match one or more selected options in each filter
    if results:
        common_product_ids = set.intersection(*results)
    else:
        common_product_ids = set()

    # filters common_product_ids for ids in the correct category and in the selected price range
    products = [p for p in product_list if p['id'] in common_product_ids]
    return products


# gets the filters for the category from category_attributes
def get_filter_dict(cat_id):
    filter_option_dict = {}

    # queries the category_attribute table for filters in the selected category (ex. filters for laptops)
    query = (db.category_attribute.isFilter == True) & \
            (db.category_attribute.category_id == int(cat_id))
    
    # retrieves and adds all of the attributes to a list
    rows = db(query).select(db.category_attribute.attribute_id)
    attribute_ids = [row.attribute_id for row in rows]

    # gets the product_ids for the category
    product_ids = [p['id'] for p in get_products(cat_id)]

    # retrieves product_attribute rows with only the product_ids with the category's filters
    query = (
    (db.product_attribute.product_id.belongs(product_ids)) &
    (db.product_attribute.attribute_id.belongs(attribute_ids)) &
    (db.product_attribute.attribute_id == db.attribute_description.id)
    )

    rows = db(query).select(
        db.product_attribute.attribute_value,
        db.attribute_description.attribute_name
    ) # example RAM , 16GB

    for row in rows:
        value = row.product_attribute.attribute_value
        attribute = row.attribute_description.attribute_name

        if attribute not in filter_option_dict:
            # adds the key if it doesn't exist
            filter_option_dict[attribute] = set()

        # adds to the key's list of options
        filter_option_dict[attribute].add(value)
    return filter_option_dict


# Retrieves order string.
def get_order_string(order):
        order_dict = {
        'default': ' ORDER BY RANDOM()',
        'price-asc': ' ORDER BY p.price ASC',
        'price-desc': ' ORDER BY p.price DESC'
        }

        if not order:
            return ''
        else:
            return order_dict[order]


# retrieves and returns the user selected filters
def get_selected_filters(options): 

    filter_dict = {}
    # the categories are based on the original options
    categories = list(options.keys())
    categories.append('Price')
    
    # iterates through the list and sees if there is a value checked. 
    # If so, it adds that value to the dictionary under the key
    for category in categories:
        name = category + '[]'
        values = request.vars.getlist(name)
        if values:
            filter_dict[category] = values
    return filter_dict


def add_to_cart():
    # ----------------------------------
    # # Add to cart
    # ----------------------------------

    # Define the form being used
    form = SQLFORM(db.shopping_cart2)

    if form.accepts:
        # get form details
        user_id = request.vars['user_id']
        product_id = request.vars['product_id']
        session_id = request.vars['session_id']
        quantity = int(request.vars['quantity'])
        added_product = db(db.products.id == product_id).select().first()
        image = db((db.product_images.product_id == product_id) & (db.product_images.main_image == True)).select().first()
        img_src = image.image_filename
        img_alt = image.image_alt
        cat = (db(db.categories.id == added_product.category_id).select().first().category_name).lower()
        cat = cat.replace("&","").replace(" ","_")
        brand = (db(db.brand.id == added_product.brand_id).select().first()).brand_name.lower()

        product = None
        existing_quantity = 0

        # Flag
        added_successful = False

        # Flag used if the item already exists in the cart
        matched_cart = False

        # Check if user is logged in or not
        # gets the current cart on click
        cart = None
        if auth.user:
            cart = db(db.shopping_cart2.user_id == user_id).select().as_list()
        else:
            cart = db(db.shopping_cart2.session_id == session_id).select().as_list()

        # Check all cart items
        for item in cart:
            # Check if newly added item exists in the cart
            if int(item['product_id']) == int(product_id):
                # Get the current quantity in the cart
                if auth.user:
                    product = db.shopping_cart2(user_id=user_id, product_id=product_id)
                else:
                    product = db.shopping_cart2(session_id=session_id, product_id=product_id)
                
                # If exists in cart, set the existing quantity and matched_cart
                existing_quantity = int(product['quantity'])
                matched_cart = True

        # If there was a match update the quanity, otherwise add to cart
        if matched_cart:
            # get the total qty in stock
            
            total_in_stock = int(added_product.stock_qty)
            # check to make sure they're still in stock
            if existing_quantity >= total_in_stock:
                # if no more in stock, then just send them a message
                if existing_quantity > total_in_stock:
                    response.flash = XML(f"""There are only <strong>{total_in_stock}</strong> left in stock. There are <strong>{existing_quantity}</strong> in your cart.""")                    
                else:
                    response.flash = "There are no more in stock. You added the last one to your cart!"
            else:
                # if there are more in stock then add it up
                new_quantity = quantity + existing_quantity
                product.update_record(quantity=new_quantity)
                added_successful = True
            
        else:
            db.shopping_cart2.insert(user_id=user_id, product_id=product_id, quantity=quantity, session_id=session_id)
            cart_counter = shopping_cart_count()
            added_successful = True
    
    # get the cart values
    cart_counter = shopping_cart_count()
    cart_subtotal = shopping_cart_subtotal()

    success_message =   XML(f"""
                                <div class="pie mb-2">
                                    <div class="img-holder">
                                        <img src="{URL(f'static/images/{cat}/{brand}/', img_src)}">
                                    </div> 
                                    <div class="words">
                                        {quantity} × <strong>{added_product.product_name}</strong> was added to your cart.
                                    </div> 
                                </div>
                                <hr>
                                <div class="w-100">
                                    <span>{cart_counter} items in cart</span><br>
                                    <span>Cart subtotal: ${cart_subtotal:,.2f}</span>
                                </div>
                                <hr>
                                <div class="w-100">
                                    <a class="btn btn-secondary w-100 flash-cart-btn" href="{URL('default','shopping_cart2')}">
                                        Go to cart
                                    </a>
                                </div>
                                """)

    if added_successful:          
        response.flash = success_message
    
    # hacky fix for flash response, turns html into html
    # last line "cart counter" updates the cart_counter
    response.js = '''
                $(document).ready(function() {
                    var flashDiv = $(".w2p_flash");
                    if (flashDiv.length && flashDiv.html()) {
                        var content = flashDiv.html()
                            .replace(/&lt;/g, "<")
                            .replace(/&gt;/g, ">")
                            .replace(/&amp;/g, "&");
                        flashDiv.html(content);
                    } 
                });
                ''' + f'$("#cart-counter").text("{cart_counter}");' 
                

    return locals()


def shopping_cart2():
    response.title=f'MISE - Shopping Cart'


    # ----------------------------------
    # # Quantity update logic
    # ----------------------------------


    # get values from form after clicking "update quanity" or "remove"
    # if request.post_vars:
    #     # VARIABLES
    #     session_id = response.session_id
    #     user_id = auth.user_id
    #     quantity = request.post_vars['quantityAmt']
    #     product_id = request.post_vars['product_id']
    #     product = None
        

    #     # Check if a user is logged in, use user_id or session_id
    #     if auth.user:
    #         product = db.shopping_cart2(user_id=user_id, product_id=product_id)
    #     else:
    #         product = db.shopping_cart2(session_id=session_id, product_id=product_id)

    #     # Delete a cart item if quantity is 0, or update record
    #     if not int(quantity):
    #         product.delete_record()
    #     else:
    #         # print(product)
    #         product.update_record(quantity=quantity)

    #     response.flash = f"Your cart was updated via shopping_cart!"
    
    # update the cart counter
    cart_counter = shopping_cart_count()
    response.js = f'$("#cart-counter").text("{cart_counter}");'


    # ----------------------------------
    # # Retrieve all the items in the cart
    # ----------------------------------

    # Check if the user is logged in
    where_stmt = ""
    if auth.user:
        where_stmt = f"sc.user_id = {str(auth.user.id)}"
    else:
        where_stmt = f"sc.session_id = '{str(response.session_id)}'"

    # Get the items from the database
    query = "SELECT sc.* FROM shopping_cart2 AS sc WHERE " + where_stmt
    cart_items = db.executesql(query, as_dict=True)
    subtotal = 0
    total_items = 0

    for item in cart_items:
        product_id= item['product_id']
        product = db(db.products.id == product_id).select().first()
        subtotal += (float(product['price']) * int(item['quantity']))
        total_items += int(item['quantity'])
        

    config = db(db.config).select().first()
    tax = float(config['tax'])
    tax_amt = tax * subtotal
    total = tax_amt + subtotal

    return locals()


def update_cart():
    # ----------------------------------
    # # Quantity update logic
    # ----------------------------------

    # get values from form after clicking "update quanity" or "remove"

    if request.post_vars:
        # VARIABLES
        session_id = request.post_vars['session_id']
        user_id = request.post_vars['user_id']
        quantity = request.post_vars['quantityAmt']
        product_id = request.post_vars['product_id']
        product = None

        # Check if a user is logged in, use user_id or session_id
        if auth.user:
            product = db.shopping_cart2(user_id=user_id, product_id=product_id)
        else:
            product = db.shopping_cart2(session_id=session_id, product_id=product_id)

        # Delete a cart item if quantity is 0, or update record
        if not int(quantity):
            product.delete_record()
        else:
            # print(product)
            product.update_record(quantity=quantity)

    # ----------------------------------
    # # Retrieve all the items in the cart
    # ----------------------------------

    # Check if the user is logged in
    where_stmt = ""
    if auth.user:
        where_stmt = f"sc.user_id = {str(auth.user.id)}"
    else:
        where_stmt = f"sc.session_id = '{str(response.session_id)}'"

    # Get the items from the database
    query = "SELECT sc.* FROM shopping_cart2 AS sc WHERE " + where_stmt
    cart_items = db.executesql(query, as_dict=True)
    subtotal = 0
    total_items = 0

    for item in cart_items:
        product_id= item['product_id']
        product = db(db.products.id == product_id).select().first()
        subtotal += (float(product['price']) * int(item['quantity']))
        total_items += int(item['quantity'])
    
    config = db(db.config).select().first()
    tax = float(config['tax'])
    tax_amt = tax * subtotal
    total = tax_amt + subtotal

    return response.json(dict(
        success=True,
        subtotal=subtotal,
        tax_amt=tax_amt,
        cart_total=total,
        total_items=total_items,
        product_id=product_id,
        quantity=quantity
    ))



    # # Define the form being used
    # form = SQLFORM(db.shopping_cart2)

    # # ----------------------------------
    # # # Quantity update logic
    # # ----------------------------------

    # # get values from form after clicking "update quanity" or "remove"
    # if form.accepts:
    #     # VARIABLES
    #     session_id = request.vars['session_id']
    #     user_id = request.vars['user_id']
    #     quantity = request.vars['quantityAmt']
    #     product_id = request.vars['product_id']

    #     # print(f"session_id: {session_id}")
    #     # print(f"user_id: {user_id}")
    #     # print(f"product_id: {product_id}")
    #     # print(f"quantity: {quantity}")

    #     product = None
        

    #     # Check if a user is logged in, use user_id or session_id
    #     if auth.user:
    #         product = db.shopping_cart2(user_id=user_id, product_id=product_id)
    #     else:
    #         product = db.shopping_cart2(session_id=session_id, product_id=product_id)

    #     # Delete a cart item if quantity is 0, or update record
    #     if not int(quantity):
    #         product.delete_record()
    #     else:
    #         # print(product)
    #         product.update_record(quantity=quantity)
    
    # cart_details = shopping_cart2()

    # # Update the cart counter
    # cart_counter = shopping_cart_count()

    # response.flash = f"Your cart was updated!"

    # # hacky fix for flash response, turns html into html
    # # last line "cart counter" updates the cart_counter
    # javascript_code = '''
    #             $(document).ready(function() {
    #                 var flashDiv = $(".w2p_flash");
    #                 if (flashDiv.length && flashDiv.html()) {
    #                     var content = flashDiv.html()
    #                         .replace(/&lt;/g, "<")
    #                         .replace(/&gt;/g, ">")
    #                         .replace(/&amp;/g, "&");
    #                     flashDiv.html(content);
    #                 } 
    #             });
    #             ''' + f'$("#cart-counter").text("{cart_counter}");' 
    
    # # check if there are no more products in cart
    # # if cart_counter == 0:
    # #     javascript_code += "document.getElementById('empty-message').classList.remove('d-none');"

    # response.js = javascript_code

    # if request.ajax:
    #     return dict(
    #         success=True,
    #         total_items=cart_details.get('total_items', 0),
    #         subtotal=cart_details.get('subtotal', 0),
    #         cart_counter=cart_counter,
    #         **cart_details
    #     )
    # else:
    #     return dict(**cart_details)
  

def account():
    response.title=f'MISE - Your Account'

    # select auth user database table based on current id
    user_info = db(db.auth_user.id == auth.user.id).select().first()

    # look up customer details based on the auth user id
    customer_info = db(db.customers.user_id == auth.user.id).select().first()

    # get the state for the user :
    if customer_info and customer_info.state_code and customer_info.street_1 != '':
        state = db(db.states.id == customer_info.state_code).select().first()
    else:
        # Redirect if no state_code
        redirect(URL('account_details'))

    # Fetch orders for the current user
    order = db(db.orders.user_id == user_info.id).select(orderby=~db.orders.order_date).first()
    line_items = db(db.order_line_items.order_id == order.id).select()
    from collections import defaultdict
    order_lines = defaultdict(list)

    for item in line_items:
        order_lines[item.order_id].append(item)


    return locals()

# account details page, to update account details
def account_details():
    
    # select auth user database table based on current id
    user_info = db(db.auth_user.id == auth.user.id).select().first()

    # look up user details based on the auth user id
    customer_info = db((db.customers.user_id == auth.user.id)).select().first()

    if not customer_info:
        db.customers.insert(user_id=auth.user.id, street_1='')
        customer_info = db(db.customers.user_id == auth.user.id).select().first()

    try:
        if request.vars:
            
            r = request.vars
            user_info.update_record(first_name=r.first_name, last_name=r.last_name, email=r.email)

            # Update auth.user to match
            auth.user.update(first_name=r.first_name, last_name=r.last_name, email=r.email)
                
            customer_info.update_record(
                                    street_1 = r.street_1, 
                                    street_2 = r.street_2, 
                                    city = r.city,
                                    state_code = r.state,
                                    zip = r.zip,                            
                                    phone = r.phone
                                    )
            # print("requested end")
        
    except:
        pass
    
    # after updating the data, we put you back to the account page
    if request.vars:
        redirect(URL('account'))

    response.title=f'MISE - Account Details for {user_info.first_name}'
    return locals()

# ---- Order History -----
@auth.requires_login()
def order_history():
    response.title=f'MISE - Your Order History'

    user_id = auth.user.id

    # Fetch orders for the current user
    orders = db(db.orders.user_id == user_id).select(orderby=~db.orders.order_date)

    # If no orders found, just return
    if not orders:
        return dict(orders=[], order_lines={})

    # Collect order IDs
    order_ids = [order.id for order in orders]

    # Fetch line items
    line_items = db(db.order_line_items.order_id.belongs(order_ids)).select()

    # Group items by order_id
    from collections import defaultdict
    order_lines = defaultdict(list)
    for item in line_items:
        order_lines[item.order_id].append(item)

    return dict(orders=orders, order_lines=order_lines)


def build_shipping_form():

    user_info = None
    customer_info = None
    customer_state = None

    if auth.user:
        # get user details
        # select auth user database table based on current id
        user_info = db(db.auth_user.id == auth.user.id).select().first()
        # look up customer details based on the auth user id
        customer_info = db(db.customers.user_id == auth.user.id).select().first()
        # get the state for the user
        customer_state = db(db.states.id == customer_info.state_code).select().first().id

    # build the shipping form
    # Note the "default=" line is checking to see if user_info or customer_info exists and if it does, then it is filling the default value, if not, then it is blank
    shipping_form = SQLFORM.factory(
                Field('first_name', 
                      label="First Name", 
                      default=(user_info.first_name if user_info else ""), 
                      requires=IS_NOT_EMPTY()),
                Field('last_name', 
                      label="Last Name", 
                      default=(user_info.last_name if user_info else ""),
                      requires=IS_NOT_EMPTY()),
                Field('street_1', 
                      label="Address Line 1",
                      default=(customer_info.street_1 if customer_info else ""), 
                      requires=IS_NOT_EMPTY()),
                Field('street_2', 
                      label="Address Line 2",
                      default=(customer_info.street_2 if customer_info else "")),
                Field('city', 
                      label="City",
                      default=(customer_info.city if customer_info else ""),
                      requires=IS_NOT_EMPTY()),
                Field('state', 'reference states', 
                      label="State", 
                      default=(customer_state or 0), 
                      requires=IS_IN_DB(db, 'states.id', '%(state_name)s', zero="Choose a state...", error_message='Pick a state')),
                Field('zip', 
                      label="Zip Code",
                      default=(customer_info.zip if customer_info else ""), 
                      requires=IS_NOT_EMPTY()),
                Field('email',
                      label="Email",
                      default=(user_info.email if user_info else ""),
                      requires=IS_EMAIL()),
                Field('user_id',
                      default=(auth.user.id if auth.user else response.session_id)),
                _class='order-forms w-100 px-3',
                _name='shipping-info',
                _id='shipping-info',
                formname="shipping"
            )
    
    # set the user_id field to hidden
    shipping_form.custom.widget.user_id['_type'] = 'hidden'
    # shipping_form.custom.widget.first_name['_class'] = 'form-control string input-error'

    # give the shipping form placeholders
    shipping_form.custom.widget.first_name['_placeholder'] = "John"
    shipping_form.custom.widget.last_name['_placeholder'] = "Doe"
    shipping_form.custom.widget.street_1['_placeholder'] = "123 Main St."
    shipping_form.custom.widget.street_2['_placeholder'] = "Apt. 1"
    shipping_form.custom.widget.city['_placeholder'] = "Anywhere"
    shipping_form.custom.widget.zip['_placeholder'] = "12345"
    shipping_form.custom.widget.email['_placeholder'] = "email@web.com"

    # needed to generate _formkey
    shipping_form.process()
    
    return shipping_form


def build_billing_form():

    # Check if logged in to set collapse
    collapse = "collapse show"
    if auth.user:
        collapse = "collapse"

    # build the billing form
    billing_form = SQLFORM.factory(
                Field('first_name', 
                      label="First Name", 
                      requires=IS_NOT_EMPTY()),
                Field('last_name', 
                      label="Last Name",
                      requires=IS_NOT_EMPTY()),
                Field('street_1', 
                      label="Address Line 1", 
                      requires=IS_NOT_EMPTY()),
                Field('street_2', 
                      label="Address Line 2"),
                Field('city', 
                      label="City",
                      requires=IS_NOT_EMPTY()),
                Field('state', 'reference states', 
                      label="State", 
                      requires=IS_IN_DB(db, 'states.id', '%(state_name)s', zero="Choose a state...", error_message='Pick a state')),
                Field('zip', 
                      label="Zip Code", 
                      requires=IS_NOT_EMPTY()),
                _class=f'order-forms w-100 px-3 {collapse}',
                _name='billing-info',
                _id='billing-info',
                formname="billing"
            )
    
    # give the  form placeholders
    billing_form.custom.widget.first_name['_placeholder'] = "John"
    billing_form.custom.widget.last_name['_placeholder'] = "Doe"
    billing_form.custom.widget.street_1['_placeholder'] = "123 Main St."
    billing_form.custom.widget.street_2['_placeholder'] = "Apt. 1"
    billing_form.custom.widget.city['_placeholder'] = "Anywhere"
    billing_form.custom.widget.zip['_placeholder'] = "12345"

    # needed to generate formkey
    billing_form.process()

    return billing_form


def create_payment_intent():
    """Create a payment intent for the Payment Element"""
    try:
        # Get the total amount from the session or calculate it
        session_id = response.session_id
        
        # Calculate total (same logic as in checkout)
        subtotal = 0
        total_items = 0
        
        # Determine if a user is logged in
        where_stmt = ""
        if auth.user:
            where_stmt = f"sc.user_id = {str(auth.user.id)}"
        else:
            where_stmt = f"sc.session_id = '{str(response.session_id)}'"

        # GET THE CART
        cart_query = "SELECT sc.* FROM shopping_cart2 AS sc WHERE " + where_stmt
        cart_items = db.executesql(cart_query, as_dict=True)
        
        for item in cart_items:
            product_id = item['product_id']
            product = db(db.products.id == product_id).select().first()
            subtotal += (float(product['price']) * int(item['quantity']))
            total_items += int(item['quantity'])

        config = db(db.config).select().first()
        tax = float(config['tax'])
        tax_amt = tax * subtotal
        total = tax_amt + subtotal
        
        # Convert to cents
        amount_in_cents = int(total * 100)
        
        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency='usd',
            metadata={
                'user_id': auth.user.id if auth.user else 'guest',
                'session_id': session_id,
                'order_number': config.order_number
            },
            automatic_payment_methods={'enabled': True}
        )
        
        return response.json({
            'client_secret': intent.client_secret,
            'amount': amount_in_cents,
            'currency': 'usd'
        })
        
    except Exception as e:
        return response.json({'error': str(e)})


def checkout():
    response.title=f'MISE - Checkout'

    print(f"{'NEW RUN':=^120}")
    # VARIABLES
    session_id = response.session_id
    user_id = auth.user_id
    config = db(db.config).select().first()
    order_number = config.order_number
    subtotal = 0
    total_items = 0

    # ----------------------------------
    # # Build the cart items list/receipt
    # ----------------------------------

    # determine if a user is logged in
    where_stmt = ""
    if auth.user:
        where_stmt = f"sc.user_id = {str(auth.user.id)}"
    else:
        where_stmt = f"sc.session_id = '{str(response.session_id)}'"

    # GET THE CART, and then start adding up items
    cart_query = "SELECT sc.* FROM shopping_cart2 AS sc WHERE " + where_stmt
    cart_items = db.executesql(cart_query, as_dict=True)
    
    for item in cart_items:
        product_id = item['product_id']
        product = db(db.products.id == product_id).select().first()
        subtotal += (float(product['price']) * int(item['quantity']))
        total_items += int(item['quantity'])

    # Calculate shipping cost
    if total_items:
        shipping = calculate_shipping(total_items)
    else:
        shipping = 1

    tax = float(config['tax'])
    tax_amt = tax * (subtotal + shipping)
    total = tax_amt + subtotal

    # ----------------------------------
    # # Form processing and Validation
    # ----------------------------------

    # create forms
    shipping_form = build_shipping_form()
    billing_form = build_billing_form()
    
    # set data to a value so it doesn't error
    shipping_data = {}
    billing_data = {}

    # get json data from ajax call (when place-order button is clicked)
    if request.env.request_method == 'POST' and request.body:

        try:
            json_body = request.body.read()
            request.body.seek(0)
            all_forms_data = json.loads(json_body)
            # DEBUG
            print("Received data:", all_forms_data)
            
        except Exception as e:
            # DEBUG
            print("JSON parsing error:", e)

            # If JSON parsing fails, return an error message
            session.flash = 'Invalid JSON data received.'
            return json.dumps(dict(status='error', message=f'Invalid JSON data received: {e}'))
        
        # separate out the data based on which form it's from
        shipping_data = Storage(all_forms_data.get('shipping-info', {}))
        billing_data = Storage(all_forms_data.get('billing-info', {}))
        payment_intent_id = all_forms_data.get('payment_intent_id')
        validate_only = all_forms_data.get('validate_only', False)
        payment_validation_success = all_forms_data.get('payment_validation_success')
        

        # DEBUG: Log the separated data
        print("Shipping data:", shipping_data)
        print("Shipping data form key:", shipping_data._formkey)
        print("Billing data:", billing_data)
        print("Payment Intent ID:", payment_intent_id)
        print("Validate only:", validate_only)
        print("Payment validation success:", payment_validation_success)

        # validate the data
        s_accepted = shipping_form.accepts(shipping_data, session)
        b_accepted = billing_form.accepts(billing_data, session)    

        # DEBUG: Log validation results
        print("Shipping form accepted:", s_accepted)
        print("Billing form accepted:", b_accepted)
           

        # VALIDATION STEP - Just validate forms, don't process payment
        if validate_only:
            
            if s_accepted and b_accepted:
                # DEBUG
                print("Validation passed - forms are valid")

                if not payment_validation_success:
                    # Generate new keys to send too
                    new_keys = {
                        'shipping-info': shipping_form.formkey,
                        'billing-info': billing_form.formkey
                    }
                    # DEBUG LOG NEW KEYS
                    print('new keys were created and sent')
                    return json.dumps(dict(new_keys=new_keys))
                
                # Creating new keys just incase payment processing fails
                new_keys = {
                        'shipping-info': shipping_form.formkey,
                        'billing-info': billing_form.formkey
                    }

                validation_success = True
                return json.dumps(dict(status='validation_success', new_keys=new_keys))
            else:
                # DEBUG: Log errors
                print("Validation failed - form errors found")
                print("Shipping errors:", shipping_form.errors)

                # Generate a dictionary of errors to send back
                errors_dict = {}
                if shipping_form.errors:
                    errors_dict.update({shipping_form.attributes['_name']: shipping_form.errors})
                if billing_form.errors:
                    errors_dict.update({billing_form.attributes['_name']: billing_form.errors})

                # Generate new keys to send too
                new_keys = {
                    'shipping-info': shipping_form.formkey,
                    'billing-info': billing_form.formkey
                }

                return json.dumps(dict(status='error', errors=errors_dict, new_keys=new_keys))

        # FINAL PROCESSING STEP - Forms are valid, payment is confirmed, complete the order
        elif payment_intent_id:
            last4 = None
            card_brand = None
            
            # ----------------------------------
            # # Stripe Payment verification
            # ----------------------------------
            # debug 
            print("z30=inside final processing")
            try:
                # Retrieve the payment intent to confirm it was successful
                intent = stripe.PaymentIntent.retrieve(
                    payment_intent_id,
                    expand=['payment_method']
                    )
                
                # Get payment method type
                payment_method_type = intent.payment_method.type
                print(f"Payment method type: {payment_method_type}")
                
                # Handle different payment method types
                if payment_method_type == 'card':
                    last4 = intent.payment_method.card.last4
                    card_brand = intent.payment_method.card.display_brand
                elif payment_method_type == 'klarna':
                    # For Klarna, we don't have card details
                    last4 = None
                    card_brand = 'Klarna'
                elif payment_method_type == 'afterpay_clearpay':
                    last4 = None
                    card_brand = 'Afterpay'
                elif payment_method_type == 'affirm':
                    last4 = None
                    card_brand = 'Affirm'
                else:
                    # For other payment methods, use the type as the brand
                    last4 = None
                    card_brand = payment_method_type.replace('_', ' ').title()
                
                # DEBUG: Log payment intent details
                print("Payment Intent Status:", intent.status)
                print("Payment Intent ID:", intent.id)
                print("Payment Intent Amount:", intent.amount)
                print("Payment Method Type:", payment_method_type)
                print("Card Brand:", card_brand)
                print("Last 4:", last4)

                # Check if payment was successful
                if intent.status != 'succeeded':
                    # DEBUG
                    print("Payment not successful, status:", intent.status)
                    return json.dumps(dict(
                        status='error',
                        stripe_error='Payment was not successful. Please try again.'
                    ))
                
                # Store payment intent ID for reference
                charge_id = intent.id

            except stripe.error.StripeError as e:
                # DEBUG
                print("Stripe error:", e)
                return json.dumps(dict(
                    status='error',
                    stripe_error=str(e.user_message) if hasattr(e, 'user_message') else str(e)
                ))
            except Exception as e:
                # DEBUG
                print("Unexpected error:", e)
                return json.dumps(dict(
                    status='error',
                    stripe_error='An unexpected error occurred. Please try again.'
                ))

            # ----------------------------------
            # # Database Entry (only if payment is successful)
            # ----------------------------------

            response.flash = 'Order accepted.'

            # Add order to orders table
            order_id = db.orders.insert(
                order_number=order_number,
                user_id=auth.user.id if auth.user else None,
                session_id=session_id,
                total_items=total_items,
                subtotal=subtotal,
                tax=tax_amt,
                total_cost=total,
                stripe_charge_id=charge_id
                )

            # Insert into relevant databases
            if order_id:
                # Add each order_line_item
                for item in cart_items:
                    product = db(db.products.id == item['product_id']).select().first()
                    db.order_line_items.insert(
                        order_id=order_id,
                        order_number=order_number,
                        product_id=product.id,
                        price=product.price,
                        quantity_of_item=item['quantity']
                    )

                    # then deduct qty from product listing
                    new_qty = int(product.stock_qty) - int(item['quantity'])
                    product.update_record(stock_qty=new_qty)


                # Add a record to Shipping Address table
                db.shipping_address.insert(
                    street_1=shipping_data.street_1,
                    street_2=shipping_data.street_2,
                    city=shipping_data.city,
                    zip=shipping_data.zip,
                    state_code=shipping_data.state,
                    email=shipping_data.email,
                    order_id=order_id
                )

                # Add a record to Billing Address table
                db.billing_address.insert(
                    street_1=billing_data.street_1,
                    street_2=billing_data.street_2,
                    city=billing_data.city,
                    zip=billing_data.zip,
                    state_code=billing_data.state,
                    order_id=order_id
                )

                # Add payment info
                db.payment_info.insert(
                    order_id=order_id,
                    card_brand=card_brand,
                    cc_last_four=last4  # Will be None for non-card payments
                )

                # figure out date, if sunday, go to next day
                future_date = datetime.now() + timedelta(days=5)
                if (future_date.weekday()) == 6:
                    future_date += timedelta(days=1)

                # Add shipping info
                db.shipping_info.insert(
                    order_id=order_id,
                    tracking_number=random.randint(10000000000000000,100000000000000000),
                    arrival_date=future_date
                )

                # Clear shopping cart after success
                if auth.user:
                    db(db.shopping_cart2.user_id == auth.user.id).delete()
                else:
                    db(db.shopping_cart2.session_id == session_id).delete()

            else:
                response.flash = "Failed to create order."
                return json.dumps(dict(
                    status='error', 
                    stripe_error='Order creation failed. Please contact support.'
                ))

            # Set up email info
            thank_you_details = {
                'order_id': order_id,
                'order_number': order_number,
                'total': total,
                'email': shipping_data.email,
                'last4': last4,
                'payment_method': card_brand
            }

            session.ty = thank_you_details

            # After all the entries have been made: update the config order number
            update_order_num = db(db.config.id == 1).select().first()
            order_number+=1
            update_order_num.update_record(order_number=order_number)

            return json.dumps(dict(status='success', redirect_url=URL('default', 'thankyou'), thank_you_details=thank_you_details))  
        
        else:
            # Fallback
            response.flash = 'Please fill out the form correctly.'
            return json.dumps(dict(status='error', stripe_error='Please fill out the form correctly.'))
    
    return dict(
        locals(), 
        shipping_form=shipping_form, 
        billing_form=billing_form,
        stripe_publishable_key=STRIPE_PUBLISHABLE_KEY,
        amount=int(total * 100) if 'total' in locals() else 1000,
        currency='usd'
        )


def thankyou():
    response.title=f'MISE - Thank you!'

    # Get shipping info
    if session.ty:
        shipping_info = db(db.shipping_info.order_id == session.ty['order_id']).select().first()
        date_object = shipping_info.arrival_date
        arrives = date_object.strftime("%A, %B %d, %Y")


    return locals()


def order_confirmation_email():
    
    # ----------------------------------
    # # Send confirmation email
    # ----------------------------------

    mise_host_url = "http://127.0.0.1:8000/misecomputers/default/"
    img_host_url = "https://www.ianzainea.com/mise/images/"

    # Begin building the email message
    email_message = f'<html lang="en"><head></head><body style="box-sizing: border-box;"><div style="width:800px; margin:0 auto; border-radius: 6px; overflow: clip;"><div style="padding:16px; background-color: hsl(203, 81%, 83%); text-align: center;"><a href="http://127.0.0.1:8000/misecomputers/default/index" target="_blank"><img src="https://www.ianzainea.com/mise/images/miselogolong2.png" alt="MISE logo" style="width:250px;"></a></div><div style="background-color: hsl(0, 0%, 98%); padding:16px;"><h1>Thank you for your order with MISE Computers</h1>'
                                    
    # Put in order number
    email_message += f'<p>Your order number is <strong>#{session.ty["order_number"]}</strong></p>'

    # Get order
    order = db(db.orders.id == session.ty['order_id']).select().first()
    if session.ty['last4']:
        email_message += f'<p>A payment of <strong>${order.total_cost}</strong> was charged to the card ending in <strong>{session.ty["last4"]}</strong>.</p>'
    else:
        email_message += f'<p>A payment of <strong>${order.total_cost}</strong> was processed with <strong>{session.ty["payment_method"]}</strong>.</p>'

    # Get shipping info
    shipping_info = db(db.shipping_info.order_id == session.ty['order_id']).select().first()
    date_string = shipping_info.arrival_date
    date_object = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S.%f")
    arrives = date_object.strftime("%A, %B %d, %Y")

    email_message += f'<h2 style="margin-top:36px;">Shipping Details:</h2><p>Your items are expected to arrive on <strong>{arrives}</strong>.</p><p>USPS Tracking number: <strong>{shipping_info.tracking_number}</strong></p>'

    # Get order list items
    list_items = db(db.order_line_items.order_id == session.ty['order_id']).select()

    email_message += '<h2 style="margin-top:36px;">Your Items:</h2>'

    for item in list_items:
        product = db(db.products.id == item.product_id).select().first()
        image = db((db.product_images.product_id == item.product_id) & (db.product_images.main_image == True)).select().first().image_filename
        cat = (db(db.categories.id == product.category_id).select().first().category_name).lower()
        cat = cat.replace("&","").replace(" ","_")
        brand = (db(db.brand.id == product.brand_id).select().first()).brand_name.lower()
        qty = item.quantity_of_item

        email_message += f'<table style="background-color: hsl(0, 0%, 100%); width:100%; border:1px solid hsl(39, 100%, 50%); border-radius: 4px; overflow: clip; background-clip:border-box; margin:25px 0px;"><tr><td rowspan="3" style="width:30%;"><img src="https://www.ianzainea.com/mise/images/{cat}/{brand}/{image}" alt="image of {product.product_name}" style="width:100%; display: block; border-radius: 0 4px 4px;"></td><td colspan="2" style="padding:16px; vertical-align: bottom;"><h3 style="margin:0;padding:0;">{product.product_name}</h3></td></tr><tr><td style="padding:0 16px; vertical-align: top;"> Price: {product.price} </td><td style="padding: 0 16px; vertical-align: top;"> Qty: <strong>{qty}</strong></td></tr><tr><td colspan="2"><p>&nbsp;</p></td></tr></table>'

    # Add end of html
    email_message += f'<p style="margin-top:30px;text-align:center; width:100%;">Thanks again for shopping with us! See you again soon!</p></div><p style="margin-top:30px;text-align:center;">MISE Computers &copy;{datetime.now().year}</p></div></body></html>'
        
    # Send email!
    mail.send(
        to=session.ty['email'],
        subject=f'Confirmation of order #{session.ty['order_number']} from MISE Computers',
        message=email_message
    )

    if session.ty:
        del session.ty

    return locals()























# ---- Action for login/register/etc (required for auth) -----
def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    http://..../[app]/default/user/bulk_register
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    also notice there is http://..../[app]/appadmin/manage/auth to allow administrator to manage users
    """
    return dict(form=auth())

# ---- action to server uploaded static content (required) ---
@cache.action()
def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request, db)

# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

# ---- example index page ----
from gluon import *
import datetime


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

# Page Views

def index():
    response.flash = T("Hello World")
    session.forced = True
    categories = db(db.categories).select()
    return dict(message=T('Welcome to web2py!'), categories=categories)

def testmdb():
    response.view="testmdb.html"
    return locals()

def indexmise():
    response.view="indexmise.html"
    return locals()


def layoutmise():
    response.view="layoutmise.html"
    return locals()

def privacy():
    response.view="privacy.html"
    return locals()

def terms():
    response.view="terms.html"
    return locals()

def search():
    form = FORM(INPUT(_name='keyword', _type='text', _placeholder='Search...'),
                INPUT(_type='submit', _value='Search'))

    results = []
    if form.process().accepted:
        keyword = form.vars.keyword
        if keyword:
            results = db((db.products.product_name.contains(keyword))).select()
                        

    return dict(form=form, results=results)



# ---- define pages ----
def laptop_test():
    response.view='laptop_test.html'
    user_info = auth.user
    first_name = user_info.first_name
    last_name = auth.user('last_name')
    sqlstmt = "SELECT products.*, product_images.image_filename, product_images.product_id, product_images.image_alt, product_images.main_image FROM products INNER JOIN product_images ON products.id = product_images.product_id WHERE product_images.main_image = 'T'"
    rows = db.executesql(sqlstmt, as_dict=True)
    return locals()


def item_page():
    item = request.args(0).split("--") # value: 2--Test-Laptop-Product-2
    product_id = item[0] # 2 
    product = db.products[product_id] # returns rows for that product id
    images = db(db.product_images.product_id == product_id).select() # grabs images that match product id

    # if request.post_vars:
    #     print(request.post_vars)
    
    # test = session.my_test
    session_id = response.session_id
    return locals()


def category_page():

    link_arg = request.args(0).split("--")
    cat_id = link_arg[0]
    cat_name_fix = ""

    # this gets the category name
    for row in db(db.categories).select():
        if row['id'] == int(cat_id):
            cat_name_fix = row['category_name'].capitalize() 
        else:
            pass

    filter_dict = get_selected_filters()
    order = request.vars.ORDER or ''
    products = filtered_products(cat_id, filter_dict, order)
    filters = get_filter_options()
    filter_options = get_filter_options()

    return locals()


def get_products(cat_id, order):
    sqlstmt = "SELECT p.*, pi.image_filename, pi.product_id, pi.image_alt, pi.main_image FROM products AS p INNER JOIN product_images AS pi ON p.id = pi.product_id WHERE pi.main_image = 'T' AND p.category_id = " + cat_id + order 
    
    products = db.executesql(sqlstmt, as_dict=True)
    return products


def filtered_products(cat_id, filter_dict, order):
    product_list = get_products(cat_id, get_order_string(order))
    results = []

    if 'Price' in filter_dict:
        price_range = filter_dict['Price'][0]
        min_price, max_price = map(float, price_range.split("--"))
        del filter_dict['Price']

        product_list = [product for product in product_list if min_price <= product['price'] <= max_price]

    if not filter_dict:
        return product_list

    for attribute, values in filter_dict.items():

        if (attribute != 'Price') and values:
                attr_row = db(db.attribute_description.attribute_name == attribute).select().first()
                
                if not attr_row:
                    continue
                rows = db((db.product_attribute.attribute_id == attr_row.id) & (db.product_attribute.attribute_value.belongs(values))).select(db.product_attribute.product_id)
                product_ids = set([row.product_id for row in rows])
                results.append(product_ids)
        
    if results:
        common_product_ids = set.intersection(*results)
    else:
        common_product_ids = set()

    products = [p for p in product_list if p['id'] in common_product_ids]
        
    return products

# eventually should filter categories and options dynamically by 
# querying category attributes. Will keep here
def get_filter_options():
    filter_options = {
        'CPU': ['Intel i5', 'Intel i7', 'AMD Ryzen 5', 'AMD Ryzen 7'],
        'RAM' : ['8 GB', '16 GB', '32 GB'],
        'Screen Size[]' : ['13"', '15"', '17"']
    }
    return filter_options

def get_order_string(order):
        order_dict = {
        'default': ' ORDER BY p.price ASC',
        'price-asc': ' ORDER BY p.price ASC',
        'price-desc': ' ORDER BY p.price DESC'
        }

        if not order:
            return ''
        else:
            return order_dict[order]


def get_selected_filters():
    filter_dict = {}
    # rename to "attribute" ... to avoid confusion
    categories = ['RAM', 'CPU', 'Screen Size', 'Price']
    
    for category in categories:
        name = category + '[]'
        values = request.vars.getlist(name)
        if values:
            filter_dict[category] = values

    return filter_dict


def add_to_cart():
    form = SQLFORM(db.shopping_cart2)
    print(request.vars)
    if form.accepts:
        # get form details
        user_id = request.vars['user_id']
        product_id = request.vars['product_id']
        session_id = request.vars['session_id']
        quantity = int(request.vars['quantity'])
        
        product = None
        existing_quantity = 0

        # flag used if the item already exists in the cart
        matched_cart = False

        # if logged in, use the user id, if not, use the session_id
        # gets the current cart on click
        cart = None
        if auth.user:
            cart = db(db.shopping_cart2.user_id == user_id).select().as_list()
        else:
            cart = db(db.shopping_cart2.session_id == session_id).select().as_list()

        # check all cart items
        for item in cart:
            # if the currently clicked item matches on in the cart already
            if int(item['product_id']) == int(product_id):
                # check if logged in, get the current quantity in the cart
                if auth.user:
                    product = db.shopping_cart2(user_id=user_id, product_id=product_id)
                else:
                    product = db.shopping_cart2(session_id=session_id, product_id=product_id)
                
                # if matched, set the existing quantity and matched_cart
                existing_quantity = int(product['quantity'])
                matched_cart = True

        # if there was a match, then update the quanity, otherwise add to cart
        if matched_cart:
            new_quantity = quantity + existing_quantity
            product.update_record(quantity=new_quantity)
        else:
            db.shopping_cart2.insert(user_id=user_id, product_id=product_id, quantity=quantity, session_id=session_id)

        print("product:", product)

        response.flash = "Added to cart"



def shopping_cart2():
    # get values from form
    if request.post_vars:
        session_id = response.session_id
        user_id = auth.user_id
        quantity = request.post_vars['quantityAmt']
        product_id = request.post_vars['product_id']
        product = None
        # print(f"product: {product_id}, quantity: {quantity}, user_id: {user_id}, session_id: {session_id}")

        # if logged in, use the user id, if not, use the session_id
        if auth.user:
            product = db.shopping_cart2(user_id=user_id, product_id=product_id)
        else:
            product = db.shopping_cart2(session_id=session_id, product_id=product_id)

        # if the quanity is 0, then delete it, otherwise, update the quantity
        if not int(quantity):
            product.delete_record()
        else:
            # print(product)
            product.update_record(quantity=quantity)
            
    # here we get the results from the database table, based on if the user is logged in or not
    where_stmt = ""
    if auth.user:
        where_stmt = f"sc.user_id = {str(auth.user.id)}"
    else:
        where_stmt = f"sc.session_id = '{str(response.session_id)}'"

    # here we fetch it, and then start adding up items
    query = "SELECT sc.* FROM shopping_cart2 AS sc WHERE " + where_stmt
    cart_items = db.executesql(query, as_dict=True)
    subtotal = 0
    total_items = 0

    for item in cart_items:
        product_id= item['product_id']
        product = db(db.products.id == product_id).select().as_list()[0]
        subtotal += (float(product['price']) * int(item['quantity']))
        total_items += int(item['quantity'])


    return locals()


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
    
    print(total_items)

    return locals()


def account():
    # select auth user database table based on current id
    user_info = db(db.auth_user.id == auth.user.id).select().first()

    # look up customer details based on the auth user id
    customer_info = db(db.customers.user_id == auth.user.id).select().first()

    # get the state for the user
    state = db(db.states.id == customer_info.state_code).select().first()

    return locals()

# account details page, to update account details
def account_details():
    # select auth user database table based on current id
    user_info = db(db.auth_user.id == auth.user.id).select().first()

    # look up user details based on the auth user id
    customer_info = db(db.customers.user_id == auth.user.id).select().first()

    try:
        if request.vars:
            
            r = request.vars
            user_info.update_record(first_name=r.first_name, last_name=r.last_name)
            customer_info.update_record(
                                    street_1 = r.street_1, 
                                    street_2 = r.street_2, 
                                    city = r.city,
                                    state_code = r.state,
                                    zip = r.zip,                            
                                    phone = r.phone
                                    )
            print("requested end")
        
    except:
        pass
    
    # after updating the data, we put you back to the account page
    if request.vars:
        redirect(URL('account'))

    return locals()


def checkout():
    # get details from account function
    account_context = account()

    # some help building year dropdown, used on the checkout page
    current_year = datetime.datetime.now().year
    next_ten_years = []
    for i in range(10):
        next_ten_years.append(current_year + i)

    shipping_form = SQLFORM.factory(
                Field('s_first_name', 'string', label="First Name", requires=IS_NOT_EMPTY()),
                Field('s_last_name', 'string', label="Last Name", requires=IS_NOT_EMPTY()),
                Field('s_street_1', 'string', label="Address Line 1", requires=IS_NOT_EMPTY()),
                Field('s_street_2', 'string', label="Address Line 2", requires=IS_NOT_EMPTY()),
                Field('s_city', 'string', label="City", requires=IS_NOT_EMPTY()),
                Field('s_state', 'reference states', label="State", requires=IS_IN_DB(db, 'states.id', '%(state_name)s', zero="Choose a state...")),
                Field('s_zip', 'string', label="Zip Code", requires=IS_NOT_EMPTY()),
            )
    shipping_form.process(formstyle='bootstrap4_stacked')



    print("checkout:", request.vars)

    session_id = response.session_id
    user_id = auth.user_id
    config = db(db.config).select().as_list()[0]
    order_num = int(config['order_number'])
    subtotal = 0
    total_items = 0
    
    
    # determine if a user is logged in
    where_stmt = ""
    if auth.user:
        where_stmt = f"sc.user_id = {str(auth.user.id)}"
    else:
        where_stmt = f"sc.session_id = '{str(response.session_id)}'"

    # here we fetch the cart, and then start adding up items
    cart_query = "SELECT sc.* FROM shopping_cart2 AS sc WHERE " + where_stmt
    cart_items = db.executesql(cart_query, as_dict=True)
    
    for item in cart_items:
        product_id = item['product_id']
        product = db(db.products.id == product_id).select().as_list()[0]
        subtotal += (float(product['price']) * int(item['quantity']))
        total_items += int(item['quantity'])

    tax = float(config['tax'])
    tax_amt = tax * subtotal
    total = tax_amt + subtotal
    return dict(locals(), **account_context)



def display_form():
    form = FORM('Your name:', INPUT(_name='name'), INPUT(_type='submit'))
    return dict(form=form) 







# mise grid pages
@auth.requires_login()
def customers():
    grid = SQLFORM.grid(db.customers)
    return dict(grid=grid)



@auth.requires_login()
def states():
    grid = SQLFORM.grid(db.states)
    return dict(grid=grid)


@auth.requires_login()
def orders():
    grid = SQLFORM.grid(db.orders)
    return dict(grid=grid)


@auth.requires_login()
def order_line_items():
    grid = SQLFORM.grid(db.order_line_items)
    return dict(grid=grid)


@auth.requires_login()
def line_item_attributes():
    grid = SQLFORM.grid(db.line_item_attributes)
    return dict(grid=grid)

@auth.requires_login()
def payment_info():
    grid = SQLFORM.grid(db.payment_info)
    return dict(grid=grid)

@auth.requires_login()
def payment_type():
    grid = SQLFORM.grid(db.payment_type)
    return dict(grid=grid)

@auth.requires_login()
def shopping_cart():
    grid = SQLFORM.grid(db.shopping_cart)
    return dict(grid=grid)

@auth.requires_login()
def shopping_cart_attribute():
    grid = SQLFORM.grid(db.shopping_cart_attribute)
    return dict(grid=grid)

@auth.requires_login()
def products():
    grid = SQLFORM.grid(db.products)
    return dict(grid=grid)




# ---- API (example) -----
@auth.requires_login()
def api_get_user_email():
    if not request.env.request_method == 'GET': raise HTTP(403)
    return response.json({'status':'success', 'email':auth.user.email})

# ---- Smart Grid (example) -----
@auth.requires_membership('admin') # can only be accessed by members of admin groupd
def grid():
    response.view = 'generic.html' # use a generic view
    tablename = request.args(0)
    if not tablename in db.tables: raise HTTP(403)
    grid = SQLFORM.smartgrid(db[tablename], args=[tablename], deletable=False, editable=False)
    return dict(grid=grid)

# ---- Embedded wiki (example) ----
def wiki():
    auth.wikimenu() # add the wiki to the menu
    return auth.wiki() 

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

# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

# ---- example index page ----
from gluon import *

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
    sqlstmt = "SELECT p.*, pi.image_filename, pi.product_id, pi.image_alt, pi.main_image FROM products AS p INNER JOIN product_images AS pi ON p.id = pi.product_id WHERE pi.main_image = 'T' AND p.category_id = " + cat_id 
    for row in db(db.categories).select():
        if row['id'] == int(cat_id):
            cat_name_fix = row['category_name'].capitalize() 
        else:
            pass
    products = db.executesql(sqlstmt, as_dict=True)
    return locals()


def add_to_cart():
    form = SQLFORM(db.shopping_cart2)
    if form.accepts:
        user_id = request.vars['user_id']
        product_id = request.vars['product_id']
        session_id = request.vars['session_id']
        quantity = request.vars['quantity']
        db.shopping_cart2.insert(user_id=user_id, product_id=product_id, quantity=quantity, session_id=session_id)
        product = db.products[product_id]
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


# useful info:
# print(response.session_id)
# print(auth.user_id)

# db.define_table('orders',
#                 Field('order_number', 'integer', length=10, notnull=True, unique=True, required=True),
#                 Field('user_id', 'reference auth_user', default='auth.user_id'),
#                 Field('order_date'),
#                 Field('ship_date'),
#                 Field('subtotal', 'decimal(7,2)'),
#                 Field('tax', 'decimal(7,2)'),
#                 Field('shipping_cost', 'decimal(7,2)'),
#                 Field('total_cost', 'decimal(7,2)'),
#                 Field('status'),
#                 Field('tracking_number'),
#                 )


def checkout():
    session_id = response.session_id
    user_id = auth.user_id
    config = db(db.config).select().as_list()[0]
    order_num = int(config['order_number'])
    subtotal = 0
    total_items = 0
    
    

    where_stmt = ""
    if auth.user:
        where_stmt = f"sc.user_id = {str(auth.user.id)}"
    else:
        where_stmt = f"sc.session_id = '{str(response.session_id)}'"

    # here we fetch it, and then start adding up items
    cart_query = "SELECT sc.* FROM shopping_cart2 AS sc WHERE " + where_stmt
    cart_items = db.executesql(cart_query, as_dict=True)
    
    for item in cart_items:
        product_id= item['product_id']
        product = db(db.products.id == product_id).select().as_list()[0]
        subtotal += (float(product['price']) * int(item['quantity']))
        total_items += int(item['quantity'])

    tax = float(config['tax'])
    tax_amt = tax * subtotal
    total = tax_amt + subtotal
    return locals()



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

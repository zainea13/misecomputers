# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

# ---- example index page ----
def index():
    response.flash = T("Hello World")
    categories = db(db.categories).select()
    return dict(message=T('Welcome to web2py!'), categories=categories)

def testmdb():
    response.view="testmdb.html"
    return locals()

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
    item = request.args(0).split("--")
    product_id = item[0]
    product = db.products[product_id]
    images = db(db.product_images.product_id == product_id).select()
    return dict(product=product, images=images)

def category_page():

    link_arg = request.args(0).split("--")
    cat_id = link_arg[0]
    cat_name = ""
    sqlstmt = "SELECT products.*, product_images.image_filename, product_images.product_id, product_images.image_alt, product_images.main_image FROM products INNER JOIN product_images ON products.id = product_images.product_id WHERE product_images.main_image = 'T' AND products.category_id = " + cat_id 
    for row in db(db.categories).select():
        if row['id'] == int(cat_id):
             cat_name = row['category_name'].capitalize()           
        else:
            pass
    
    products = db.executesql(sqlstmt, as_dict=True)
                
        
    return locals()



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

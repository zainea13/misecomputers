# -*- coding: utf-8 -*-
# -------------------------------------------------------------------------
# This is a sample controller
# this file is released under public domain and you can use without limitations
# -------------------------------------------------------------------------

# ---- example index page ----
from gluon import *
import datetime
import json
from gluon.storage import Storage
from gluon.contrib.stripe import Stripe




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

def product_entry_form():
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
    

    print(f"{'new data':=^80}")

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
            print("attr_name: ", attr_name)
            print("attr_value: ", attr_value)
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

    # if request.post_vars:
    #     print(request.post_vars)
    
    # test = session.my_test
    session_id = response.session_id
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
        
        product = None
        existing_quantity = 0

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
                
                # If matched, set the existing quantity and matched_cart
                existing_quantity = int(product['quantity'])
                matched_cart = True

        # If there was a match update the quanity, otherwise add to cart
        if matched_cart:
            new_quantity = quantity + existing_quantity
            product.update_record(quantity=new_quantity)
        else:
            db.shopping_cart2.insert(user_id=user_id, product_id=product_id, quantity=quantity, session_id=session_id)

        response.flash = "Added to cart"



def shopping_cart2():
    # ----------------------------------
    # # Quantity update logic
    # ----------------------------------

    # get values from form after clicking "update quanity" or "remove"
    if request.post_vars:
        # VARIABLES
        session_id = response.session_id
        user_id = auth.user_id
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
    
    # print(total_items)

    return locals()


def account():
    # select auth user database table based on current id
    user_info = db(db.auth_user.id == auth.user.id).select().first()

    # look up customer details based on the auth user id
    customer_info = db(db.customers.user_id == auth.user.id).select().first()

    # get the state for the user : what is this line for?
    try:
        state = db(db.states.id == customer_info.state_code).select().first()
        if not state:
            state = 1
    except:
        state = 1

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
            # print("requested end")
        
    except:
        pass
    
    # after updating the data, we put you back to the account page
    if request.vars:
        redirect(URL('account'))

    return locals()


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

    # give the shipping form placeholders
    shipping_form.custom.widget.first_name['_placeholder'] = "John"
    shipping_form.custom.widget.last_name['_placeholder'] = "Doe"
    shipping_form.custom.widget.street_1['_placeholder'] = "123 Main St."
    shipping_form.custom.widget.street_2['_placeholder'] = "Apt. 1"
    shipping_form.custom.widget.city['_placeholder'] = "Anywhere"
    shipping_form.custom.widget.zip['_placeholder'] = "12345"

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



def checkout():
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

    tax = float(config['tax'])
    tax_amt = tax * subtotal
    total = tax_amt + subtotal


    # ----------------------------------
    # # Stripe form
    # ----------------------------------

  

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
            
        except Exception as e:
            # If JSON parsing fails, return an error message
            session.flash = 'Invalid JSON data received.'
            return json.dumps(dict(status='error', message=f'Invalid JSON data received: {e}'))
        
        # separate out the data based on which form it's from
        shipping_data = Storage(all_forms_data.get('shipping-info', {}))
        billing_data = Storage(all_forms_data.get('billing-info', {}))

        # validate the data
        s_accepted = shipping_form.accepts(shipping_data, session)
        b_accepted = billing_form.accepts(billing_data, session)       

        # Either redirects, or returns errors
        if s_accepted and b_accepted:
            response.flash = 'Form accepted.'

            # ----------------------------------
            # # Database Entry
            # ----------------------------------

            # Add order to orders table
            order_id = db.orders.insert(
                order_number=order_number,
                user_id=auth.user.id if auth.user else None,
                session_id=session_id,
                total_items=total_items,
                subtotal=subtotal,
                tax=tax_amt,
                total_cost=total
                )

            
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

                db.commit()
            else:
                response.flash = "Failed to create order."

            # After all the entries have been made: update the config order number
            update_order_num = db(db.config.id == 1).select().first()
            order_number+=1
            update_order_num.update_record(order_number=order_number)

            return json.dumps(dict(status='success', redirect_url=URL('default', 'thankyou')))  
        
        elif shipping_form.errors or billing_form.errors: 
            response.flash = 'The form has errors.'

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
          
        else:
            response.flash = 'Please fill out the form.'

    




    return dict(locals(), shipping_form=shipping_form, billing_form=billing_form)


def thankyou():
    return locals()

def checkout_test():
    form = build_shipping_form()
    if form.accepts(request, session):
        response.flash = 'form accepted'
    elif form.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill the form'
    return locals()


def extra_checkout_code():

    # some help building year dropdown, used on the checkout page
    current_year = datetime.datetime.now().year
    next_ten_years = []
    for i in range(10):
        next_ten_years.append(current_year + i)



    
    
    
    

    



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

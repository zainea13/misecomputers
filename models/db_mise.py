# -*- coding: utf-8 -*-
import random
from gluon.tools import Mail
from private.private import *
mail = auth.settings.mailer
mail.settings.server = 'smtp.gmail.com:465'
mail.settings.tls = True
mail.settings.sender = smtp_settings['sender']
mail.settings.login = smtp_settings['login']


db.define_table('config',
                Field('order_number', 'integer', length=10),
                Field('tax', 'decimal(7,2)'),
                Field('shipping_rate')
                )


db.define_table('states',
                Field('state_code', notnull=True, unique=True),
                Field('state_name'),
                format='%(state_code)s',
               )


db.define_table('customers',
                Field('street_1', notnull=True),
                Field('street_2'),
                Field('city'),
                Field('zip'),
                Field('state_code', 'reference states', label="State"),
                Field('phone'),
                Field('user_id', 'reference auth_user', default='auth.user_id'),
                )

# -------- PRODUCT TABLES -----------------


db.define_table('categories',
                Field('category_name', notnull=True, unique=True),
                format='%(category_name)s',
                migrate=True
                )


db.define_table('brand',
                Field('brand_name', notnull=True, unique=True),
                Field('brand_details'),
                Field('brand_logo'),
                format='%(brand_name)s',
          
                )

db.define_table('products',
                Field('product_name', notnull=True),
                Field('stock_qty', 'integer', notnull=True),
                Field('price', 'decimal(7,2)', notnull=True),
                Field('category_id', 'reference categories'),
                Field('description', 'text'),
                Field('brand_id', 'reference brand'),
                format='%(product_name)s',
                )


db.define_table('product_images',
                Field('product_id', 'reference products'),
                Field('image_filename', default=''),
                Field('image_alt'),
                Field('main_image', 'boolean'),
       
                )

db.define_table('attribute_description',
                Field('attribute_name', notnull=True, unique=True),
                Field('longhand'),
                format='%(attribute_name)s'
                )

db.define_table('product_attribute',
               Field('attribute_id', 'reference attribute_description'),
                Field('attribute_value', notnull=True),
                Field('product_id', 'reference products'),
                Field('full_description'),
                Field('is_key_feature', type='boolean', default=False)
                )            
                
db.define_table('category_attribute',
                Field('category_id', 'reference categories'),
                Field('attribute_id', 'reference attribute_description'),
                Field('isFilter', 'boolean')
                )


# ---------- ORDERS TABLES -------------------------

db.define_table('orders',
                Field('order_number', 'integer', notnull=True, unique=True),
                Field('user_id', 'reference auth_user'),
                Field('session_id'),
                Field('total_items', 'integer'),
                Field('subtotal', 'decimal(7,2)'),
                Field('tax', 'decimal(7,2)'),
                # Field('shipping_cost', 'decimal(7,2)'),
                Field('total_cost', 'decimal(7,2)'),
                Field('order_date', 'datetime', default=request.now),
                # Field('ship_date'),
                # Field('status'),
                # Field('tracking_number'),
                Field('stripe_charge_id'),
                migrate=False
                )


db.define_table('order_line_items',
                Field('order_id', 'reference orders'),
                Field('order_number', 'integer'),
                Field('product_id'),
                Field('price'),
                Field('quantity_of_item', 'integer'),
                migrate=True
                )


db.define_table('shipping_address',
                Field('street_1', notnull=True),
                Field('street_2'),
                Field('city'),
                Field('zip'),
                Field('state_code', 'reference states', label="State"),
                Field('email'),
                Field('order_id', 'reference orders'),
                migrate=True
                )


db.define_table('line_item_attributes',
                Field('line_item_id', 'reference order_line_items', default='order_line_items.id'),
                Field('attribute_id', 'reference attribute_description', default='attribute.id'),
                )

# # -------------- PAYMENTS TABLES ------------------------


db.define_table('payment_info',
                Field('order_id', 'reference orders', default='orders.id'),
                Field('card_brand'),
                Field('cc_last_four', 'integer', length=4),
                # migrate=True
                )




db.define_table('billing_address',
                Field('street_1', notnull=True),
                Field('street_2'),
                Field('city'),
                Field('zip'),
                Field('state_code', 'reference states', label="State"),
                Field('order_id', 'reference orders'),
                migrate=True
                )

# ----------------- SHOPPING CART TABLES ----------------------------

db.define_table('shopping_cart2',
                Field('user_id', 'reference auth_user', default='auth.user_id'),
                Field('product_id', 'reference products', default='products.id'),
                Field('quantity', 'integer'),
                Field('session_id')
         
                )

db.define_table('shopping_cart_attribute',
                Field('attribute_id', 'reference attribute_description', default='attribute.id'),
            
                )

# ----------------- Shipping TABLES ----------------------------
db.define_table('shipping_info',
                Field('order_id', 'reference orders', default='orders.id'),
                Field('tracking_number'),
                Field('arrival_date', 'datetime'),
                migrate=True
                )

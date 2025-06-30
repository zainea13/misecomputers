# -*- coding: utf-8 -*-

db.define_table('config',
                Field('order_number', type='integer', length=10),
                Field('tax', type='decimal(7,2)'),
                )


db.define_table('states',
                Field('state_code', type='string', notnull=True, unique=True),
                Field('state_name', type='string'),
                format='%(state_code)s',

               )


db.define_table('customers',
                Field('street_1', type='string', notnull=True),
                Field('street_2', type='string'),
                Field('city', type='string'),
                Field('zip', type='string'),
                Field('state_code', 'reference states', label="State"),
                Field('phone', type='string'),
                Field('user_id', 'reference auth_user', default='auth.user_id'),

                )

# -------- PRODUCT TABLES -----------------


db.define_table('categories',
                Field('category_name', type='string', notnull=True, unique=True),
                format='%(category_name)s',
  
                )


db.define_table('brand',
                Field('brand_name', type='string', notnull=True, unique=True),
                Field('brand_details', type='string'),
                Field('brand_logo'),
                format='%(brand_name)s',
          
                )

db.define_table('products',
                Field('product_name', type='string', notnull=True),
                Field('stock_qty', type='integer', notnull=True),
                Field('price', type='decimal(7,2)', notnull=True),
                Field('category_id', 'reference categories'),
                Field('key_features', type='list:string'),
                Field('description', type='text'),
                Field('brand_id', 'reference brand'),
                format='%(product_name)s',
        
                )


db.define_table('product_images',
                Field('product_id', 'reference products'),
                Field('image_filename', type='string'),
                Field('image_alt', type='string'),
                Field('main_image', type='boolean'),
       
                )

db.define_table('attribute_description',
                Field('attribute_name', notnull=True, unique=True),
                format='%(attribute_name)s'
                )


db.define_table('product_attribute',
                Field('attribute_id', 'reference attribute_description'),
                Field('attribute_value', type='string', notnull=True),
                Field('product_id', 'reference products')
                )




# ---------- ORDERS TABLES -------------------------

db.define_table('orders',
                Field('order_number', 'integer', length=10, notnull=True, unique=True, required=True),
                Field('user_id', 'reference auth_user', default='auth.user_id'),
                Field('order_date'),
                Field('ship_date'),
                Field('subtotal', 'decimal(7,2)'),
                Field('tax', 'decimal(7,2)'),
                Field('shipping_cost', 'decimal(7,2)'),
                Field('total_cost', 'decimal(7,2)'),
                Field('status'),
                Field('tracking_number'),
            
                )


db.define_table('order_line_items',
                Field('order_number', 'reference orders', default='orders.order_number'),
                Field('product_id', 'reference products', default='products.id'),
                Field('price', 'reference products', default='products.price'),
                Field('quantity_of_item', type='integer'),
      
                )


db.define_table('line_item_attributes',
                Field('line_item_id', 'reference order_line_items', default='order_line_items.id'),
                Field('attribute_id', 'reference attribute_description', default='attribute.id'),
     
                )

# # -------------- PAYMENTS TABLES ------------------------


db.define_table('payment_type',
                Field('pay_type', type='string'),
         
                )

db.define_table('payment_info',
                Field('order_number', 'reference orders', default='orders.order_number'),
                Field('payment_type_id', 'reference payment_type', default='payment_type.id'),
                Field('credit_card_last_four', type='integer', length=4),
             
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

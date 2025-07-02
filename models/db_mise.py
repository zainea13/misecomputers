# -*- coding: utf-8 -*-

db.define_table('config',
                Field('order_number', 'integer', length=10),
                Field('tax', 'decimal(7,2)'),
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
                Field('key_features', 'list:string'),
                Field('description', 'text'),
                Field('brand_id', 'reference brand'),
                format='%(product_name)s',
        
                )


db.define_table('product_images',
                Field('product_id', 'reference products'),
                Field('image_filename'),
                Field('image_alt'),
                Field('main_image', 'boolean'),
       
                )

db.define_table('attribute_description',
                Field('attribute_name', notnull=True, unique=True),
                format='%(attribute_name)s'
                )


db.define_table('product_attribute',
                Field('attribute_id', 'reference attribute_description'),
                Field('attribute_value', notnull=True),
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
                Field('quantity_of_item', 'integer'),
      
                )


db.define_table('line_item_attributes',
                Field('line_item_id', 'reference order_line_items', default='order_line_items.id'),
                Field('attribute_id', 'reference attribute_description', default='attribute.id'),
     
                )

# # -------------- PAYMENTS TABLES ------------------------


db.define_table('payment_type',
                Field('pay_type'),
         
                )

db.define_table('payment_info',
                Field('order_number', 'reference orders', default='orders.order_number'),
                Field('payment_type_id', 'reference payment_type', default='payment_type.id'),
                Field('credit_card_last_four', 'integer', length=4),
             
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

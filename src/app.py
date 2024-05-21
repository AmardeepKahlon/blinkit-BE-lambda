import logging
import os
import cloudinary
import cloudinary.uploader


from libs.utils import (
  token_required,
  token_required_is_admin
)
from libs import login
from libs.user import user_create
from libs.admin import admin_create
from libs.admin import (
  category as admin_category, 
  subcategory as admin_subcategory, 
  product as admin_product,
  collections as admin_collections
)
from libs.user import (
  category as user_category, 
  product as user_product, 
  subcategory as user_subcategory, 
  order
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

'''cloudinary configration to upload images'''
cloudinary.config( 
  cloud_name = os.environ['CLOUD_NAME'], 
  api_key = os.environ['API_KEY'],
  api_secret = os.environ['API_SECRET']
)

def login_handler(event, context):
  return login.login_handler(event, context)

def user_handler(event, context):
  return user_create.user_handler(event, context)

def admin_handler(event, context):
  return admin_create.admin_handler(event, context)

@token_required_is_admin
def category_handler(event, context):
  return admin_category.category_handler(event, context)

@token_required_is_admin
def category_form_handler(event, context):
  return admin_category.category_formdata_handler(event, context)

@token_required_is_admin
def subcategory_handler(event, context):
  return admin_subcategory.subcategory_handler(event, context)

@token_required_is_admin
def product_handler(event, context):
  return admin_product.product_handler(event, context)

@token_required_is_admin
def get_categories_handler(event, context):
  return admin_category.get_categories_handler(event, context)
  
@token_required_is_admin
def delete_category_handler(event, context):
  return admin_category.delete_category_handler(event, context)

@token_required_is_admin
def delete_subcategory_handler(event, context):
  return admin_subcategory.delete_subcategory_handler(event, context)
        
@token_required_is_admin
def delete_product_handler(event, context):
  return admin_product.delete_product_handler(event, context)

@token_required_is_admin
def update_category_handler(event, context):
  return admin_category.update_category_handler(event, context)

@token_required_is_admin
def get_subcategories_handler(event, context):
  return admin_subcategory.get_subcategories_handler(event, context)

@token_required_is_admin
def get_category_subcategories_handler(event, context):
  return admin_category.get_category_subcategories_handler(event, context)

@token_required_is_admin
def update_subcategory_handler(event, context):
  return admin_subcategory.update_subcategory_handler(event, context)

@token_required_is_admin
def get_products_handler(event, context):
  return admin_product.get_products_handler(event, context)
  
@token_required_is_admin
def get_subcategory_products_handler(event, context):
  return admin_subcategory.get_subcategory_products_handler(event, context)

@token_required_is_admin
def get_specific_product_handler(event, context):
  return admin_product.get_specific_product_handler(event, context)

@token_required_is_admin
def update_product_handler(event, context):
  return admin_product.update_product_handler(event, context)
    
@token_required_is_admin
def add_product_variant_handler(event, context):
  return admin_product.add_product_variant_handler(event, context)

@token_required_is_admin
def update_product_variant_handler(event, context):
  return admin_product.update_product_variant_handler(event, context)

def user_get_categories_handler(event, context):
  return user_category.get_categories_handler(event, context)

def user_get_category_subcategories_handler(event, context):
  return user_category.get_category_subcategories_handler(event, context)

def user_get_subcategory_products_handler(event, context):
  return user_subcategory.get_subcategory_products_handler(event, context)

def user_get_specific_product_handler(event, context):
  return user_product.get_specific_product_handler(event, context)

# @token_required
# def create_cart_handler(event, context):
#   return cart.create_cart_handler(event, context)

# @token_required
# def update_cart_handler(event, context):
#   return cart.update_cart_handler(event, context)

# def delete_cart_handler(event, context):
#   return cart.delete_cart_handler(event, context)

@token_required
def create_order_handler(event, context, payload):
  return order.order_handler(event, context, payload)

@token_required
def get_order_handler(event, context, payload):
  return order.get_order_handler(event, context, payload)

@token_required
def get_orders_handler(event, context, payload):
  return order.get_orders_handler(event, context, payload)

@token_required_is_admin
def collection_handler(event, context):
  return admin_collections.create_collection(event, context)

@token_required_is_admin
def get_collection_handler(event, context):
  return admin_collections.get_collection(event, context)

@token_required_is_admin
def get_collections_handler(event, context):
  return admin_collections.get_collections(event, context)

@token_required_is_admin
def update_collection_handler(event, context):
  return admin_collections.update_collection(event, context)

@token_required_is_admin
def delete_collection_handler(event, context):
  return admin_collections.delete_collection(event, context)

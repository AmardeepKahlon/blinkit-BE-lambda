import logging
import json
import os
import cloudinary
import cloudinary.uploader
import base64

from bson import ObjectId

from libs.utils import (
  token_required, 
  validate_schema
)
from config.db import db
from config.schemas import (
  product_variant_schema, 
  add_product_variant_schema
)
from libs import login
from libs.user import user_create
from libs.admin import admin_create
from libs.admin import category, subcategory, product

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

@token_required
def category_handler(event, context):
  return category.category_handler(event, context)

@token_required
def subcategory_handler(event, context):
  return subcategory.subcategory_handler(event, context)

@token_required
def product_handler(event, context):
  return product.product_handler(event, context)

@token_required
def get_categories_handler(event, context):
  return category.get_categories_handler(event, context)
  
@token_required
def delete_category_handler(event, context):
  return category.delete_category_handler(event, context)

@token_required
def delete_subcategory_handler(event, context):
  return category.delete_subcategory_handler(event, context)
        
@token_required
def delete_product_handler(event, context):
  return product.delete_product_handler(event, context)

@token_required
def update_category_handler(event, context):
  return category.update_category_handler(event, context)

@token_required
def get_subcategories_handler(event, context):
  return subcategory.get_subcategories_handler(event, context)

@token_required
def get_category_subcategories_handler(event, context):
  return category.get_category_subcategories_handler(event, context)

@token_required
def update_subcategory_handler(event, context):
  return subcategory.update_subcategory_handler(event, context)

@token_required
def get_products_handler(event, context):
  return product.get_products_handler(event, context)
  
@token_required
def get_subcategory_products_handler(event, context):
  return subcategory.get_subcategory_products_handler(event, context)

@token_required
def get_specific_product_handler(event, context):
  return product.get_specific_product_handler(event, context)

@token_required
def update_product_handler(event, context):
  return product.update_product_handler(event, context)
    
@token_required
def add_product_variant_handler(event, context):
  try:
    if 'body' in event and isinstance(event['body'], str):
      body = json.loads(event['body'])
    else:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Request body is missing or empty"})
      }
  
    is_valid, error_response = validate_schema(body, add_product_variant_schema)
    if not is_valid:
      return error_response
    selected_product = db.subcategories.find_one({"_id": product_data["_id"]})

    variants_body = body.get('variants', [])
    if not isinstance(variants_body, list):
      variants_body = [variants_body]
    if not variants_body:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Variants are missing in the request body"})
      }

    total_variants = int(selected_product['number_of_variants']) + len(variants_body)
    if total_variants > 10:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Maximum ten variants are allowed for each product"})
      }
    for variant in variants_body:
      is_valid, error_response = validate_schema(variant, product_variant_schema)
      if not is_valid:
        return error_response
    
    for variant in variants_body:
      encoded_images = variant.get('images')
      if not encoded_images or not isinstance(encoded_images, list):
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Variant Image data is missing or invalid"})
        }
      if len(encoded_images) < 1:
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "At least two images is required for each variant"})
        }
      if len(encoded_images) > 5:
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Maximum five images are allowed for each variant"})
        }
      decoded_images = [base64.b64decode(image) for image in encoded_images]
      variant['images'] = decoded_images
      
    logger.info("Received event: " + json.dumps(event, indent=2))
      
    try:
      product_data = body
      product_id = product_data.get("_id")
      if isinstance(product_id, str):
        product_data["_id"] = ObjectId(product_id)
    except json.JSONDecodeError as e:
      return {
        "statusCode": 400,
        "body": json.dumps({"message": "Invalid JSON format in request body"})
      }
    logger.info("Updating the product...")
    
    if 'image' in body:
      try:
        product_image_data = body.get('image')
        product_upload_response = cloudinary.uploader.upload(product_image_data)
        product_image_url = product_upload_response['secure_url']
        product_data['image_url'] = product_image_url
      except Exception as e:
        return {
          "statusCode": 500,
          "body": json.dumps({"message": "Failed to upload image to Cloudinary", "error": str(e)})
        }

    for variant in variants_body:
      image_urls = []
      for image_data in variant['images']:
        try:
          upload_response = cloudinary.uploader.upload(image_data)
          image_url = upload_response['secure_url']
          image_urls.append(image_url)
        except Exception as e:
          return {
            "statusCode": 500,
            "body": json.dumps({"message": "Failed to upload variant image to Cloudinary", "error": str(e)})
          }
      variant['image_urls'] = image_urls

    product_data.pop('variants', None)
    
    for variant in variants_body:
      variant.pop('images', None)
      variant['product_id'] = str(product_id)
      variant_id = db.variants.insert_one(variant).inserted_id
      logger.info(variant_id)
      variant = db.variants.find_one({"_id": variant_id})
      logger.info(variant)  
    selected_product['variants'] = variants_body
    if not selected_product:
      return {
        "statusCode": 404,
        "body": json.dumps({"message": "Category not found or not updated"})
      }
    else:
      selected_product["_id"] = str(selected_product["_id"])
      return {
        "statusCode": 200,
        "body": json.dumps({"message": "Category updated successfully", "category": selected_product})
      }
  except Exception as e:
    error_message = str(e)
    return {
      "statusCode": 500,
      "body": json.dumps({"errorMessage": error_message})
    }

@token_required
def update_product_variant_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))
  
  try:
    if 'body' in event and isinstance(event['body'], str):
      body = json.loads(event['body'])
    else:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Request body is missing or empty"})
      }
  
    is_valid, error_response = validate_schema(body, add_product_variant_schema)
    if not is_valid:
      return error_response
    selected_product = db.subcategories.find_one({"_id": product_data["_id"]})

    variants_body = body.get('variants', [])
    if not isinstance(variants_body, list):
      variants_body = [variants_body]
    if not variants_body:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Variants are missing in the request body"})
      }

    total_variants = int(selected_product['number_of_variants']) + len(variants_body)
    if total_variants > 10:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Maximum ten variants are allowed for each product"})
      }
    for variant in variants_body:
      is_valid, error_response = validate_schema(variant, product_variant_schema)
      if not is_valid:
        return error_response
    
    for variant in variants_body:
      encoded_images = variant.get('images')
      if not encoded_images or not isinstance(encoded_images, list):
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Variant Image data is missing or invalid"})
        }
      if len(encoded_images) < 1:
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "At least two images is required for each variant"})
        }
      if len(encoded_images) > 5:
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Maximum five images are allowed for each variant"})
        }
      decoded_images = [base64.b64decode(image) for image in encoded_images]
      variant['images'] = decoded_images
      
    try:
      product_data = body
      product_id = product_data.get("_id")
      if isinstance(product_id, str):
        product_data["_id"] = ObjectId(product_id)
    except json.JSONDecodeError as e:
      return {
        "statusCode": 400,
        "body": json.dumps({"message": "Invalid JSON format in request body"})
      }
    logger.info("Updating the product...")
    
    if 'image' in body:
      try:
        product_image_data = body.get('image')
        product_upload_response = cloudinary.uploader.upload(product_image_data)
        product_image_url = product_upload_response['secure_url']
        product_data['image_url'] = product_image_url
      except Exception as e:
        return {
          "statusCode": 500,
          "body": json.dumps({"message": "Failed to upload image to Cloudinary", "error": str(e)})
        }

    for variant in variants_body:
      image_urls = []
      for image_data in variant['images']:
        try:
          upload_response = cloudinary.uploader.upload(image_data)
          image_url = upload_response['secure_url']
          image_urls.append(image_url)
        except Exception as e:
          return {
            "statusCode": 500,
            "body": json.dumps({"message": "Failed to upload variant image to Cloudinary", "error": str(e)})
          }
      variant['image_urls'] = image_urls

    product_data.pop('variants', None)
    
    for variant in variants_body:
      variant.pop('images', None)
      variant['product_id'] = str(product_id)
      variant_id = db.variants.insert_one(variant).inserted_id
      logger.info(variant_id)
      variant = db.variants.find_one({"_id": variant_id})
      logger.info(variant)  
    selected_product['variants'] = variants_body
    if not selected_product:
      return {
        "statusCode": 404,
        "body": json.dumps({"message": "Category not found or not updated"})
      }
    else:
      selected_product["_id"] = str(selected_product["_id"])
      return {
        "statusCode": 200,
        "body": json.dumps({"message": "Category updated successfully", "category": selected_product})
      }
  except Exception as e:
    error_message = str(e)
    return {
      "statusCode": 500,
      "body": json.dumps({"errorMessage": error_message})
    }

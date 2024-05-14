import logging
import json
import cloudinary
import cloudinary.uploader
import base64

from bson import ObjectId

from libs.utils import (
  json_unknown_type_handler, 
  validate_schema
)
from config.db import db
from config.schemas import (
  product_schema, 
  product_variant_schema, 
  update_product_schema,
  add_product_variant_schema
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def product_handler(event, context):
  try:
    if 'body' in event and isinstance(event['body'], str):
      body = json.loads(event['body'])
      variants_body = body.get('variants', [])
      if not isinstance(variants_body, list):
        variants_body = [variants_body]
      if not variants_body:
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Variants are missing in the request body"})
        }
      if len(variants_body) > 10:
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Maximum ten variants are allowed for each product"})
        }
    else:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Request body is missing or empty"})
      }

    is_valid, error_response = validate_schema(body, product_schema)
    if not is_valid:
      return error_response
    
    for variant in variants_body:
      is_valid, error_response = validate_schema(variant, product_variant_schema)
      if not is_valid:
        return error_response
    
    encoded_image = body.get('image')
    if not encoded_image:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Product Image data is missing"})
      }
    decoded_image = base64.b64decode(encoded_image)
    body['image'] = decoded_image
    
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

    logger.info("Initializing the collections...")
    products = db.products
    variants = db.variants
    
    existing_product = products.find_one({"name": body.get("name")})
    if existing_product:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Product with this name already exists"})
      }
    
    logger.info("Creating the product...")
    try:
      product_image_data = body.get('image')
      product_upload_response = cloudinary.uploader.upload(product_image_data)
      product_image_url = product_upload_response['secure_url']
      body['image_url'] = product_image_url
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
        
    body.pop('image', None)
    body.pop('variants', None)
    
    product_id = products.insert_one(body).inserted_id
    logger.info(product_id)
    product = products.find_one({"_id": product_id})
    logger.info(product)
    
    for variant in variants_body:
      variant.pop('images', None)
      variant['product_id'] = str(product_id)
      variant_id = db.variants.insert_one(variant).inserted_id
      logger.info(variant_id)
      variant = db.variants.find_one({"_id": variant_id})
      logger.info(variant)  
    product['variants'] = variants_body
    
    return {
      "statusCode": 200,
      "body": json.dumps(product, default=json_unknown_type_handler)
    }
  except Exception as e:
    error_message = str(e)
    return {
      "statusCode": 500,
      "body": json.dumps({"errorMessage": error_message})
    }

def get_products_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  products = db.products.find({})

  product_list = []
  for product in products:
    product_id = product['_id']
    variants = db.variants.find({"product_id": str(product_id)})
    product['variants'] = list(variants)
    product_list.append(product)

  return {
    "statusCode": 200,
    "body": json.dumps(product_list, default=json_unknown_type_handler)
  }
  
def get_specific_product_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  product_id = event.get("pathParameters", {}).get("product_id")
  if not product_id:
    return {
      "statusCode": 400,
      "body": json.dumps({"message": "Product ID is required"})
    }

  product = db.products.find_one({"_id": ObjectId(product_id)})
  if not product:
    return {
      "statusCode": 404,
      "body": json.dumps({"message": "Product not found"})
    }

  variants = db.variants.find({"product_id": str(product_id)})
  product['variants'] = list(variants)

  return {
    "statusCode": 200,
    "body": json.dumps(product, default=json_unknown_type_handler)
  }
  
def update_product_handler(event, context):
  try:
    if 'body' in event and isinstance(event['body'], str):
      body = json.loads(event['body'])
    else:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Request body is missing or empty"})
      }
  
    is_valid, error_response = validate_schema(body, update_product_schema)
    if not is_valid:
      return error_response

    if 'image' in body:
      encoded_image = body.get('image')
      if not encoded_image:
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Product Image data is missing"})
        }
      decoded_image = base64.b64decode(encoded_image)
      body['image'] = decoded_image

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

    product_data.pop('image', None)
    
    updated_product = db.subcategories.find_one_and_update({"_id": product_data["_id"]}, {"$set": product_data}, return_document=True)

    if not updated_product:
      return {
        "statusCode": 404,
        "body": json.dumps({"message": "Category not found or not updated"})
      }
    else:
      updated_product["_id"] = str(updated_product["_id"])
      return {
        "statusCode": 200,
        "body": json.dumps({"message": "Category updated successfully", "category": updated_product})
      }
  except Exception as e:
    error_message = str(e)
    return {
      "statusCode": 500,
      "body": json.dumps({"errorMessage": error_message})
    }

def delete_product_handler(event, context):
  try:
    product_id = event.get('pathParameters', {}).get('product_id')

    if not product_id:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Product ID is missing in the request"})
      }

    product_id = ObjectId(product_id)

    products = db.products
    variants = db.variants

    existing_product = products.find_one({"_id": product_id})
    if not existing_product:
      return {
        "statusCode": 404,
        "body": json.dumps({"errorMessage": "Product not found"})
      }

    product_variants = variants.find({"product_id": str(product_id)})

    for variant in product_variants:
      variants.delete_one({"_id": variant["_id"]})

    products.delete_one({"_id": product_id})

    return {
      "statusCode": 200,
      "body": json.dumps({"message": "Product and its variants deleted successfully"})
    }
  except Exception as e:
    error_message = str(e)
    return {
      "statusCode": 500,
      "body": json.dumps({"errorMessage": error_message})
    }
    
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

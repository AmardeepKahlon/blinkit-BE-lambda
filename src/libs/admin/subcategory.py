import logging
import json
import cloudinary.uploader
import base64

from bson import ObjectId

from libs.utils import (
  json_unknown_type_handler, 
  validate_schema
)
from config.db import db
from config.schemas import (
  subcategory_schema, 
  update_subcategory_schema
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def subcategory_handler(event, context):
  try:
    if 'body' in event and isinstance(event['body'], str):
      body = json.loads(event['body'])
    else:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Request body is missing or empty"})
      }
    
    is_valid, error_response = validate_schema(body, subcategory_schema)
    if not is_valid:
      return error_response
    
    encoded_image = body.get('image')
    if not encoded_image:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Image data is missing"})
      }
    decoded_image = base64.b64decode(encoded_image)
    body['image'] = decoded_image
    
    logger.info("Received event: " + json.dumps(event, indent=2))

    logger.info("Initializing the collection")
    subcategories = db.subcategories
    
    existing_subcategory = subcategories.find_one({"name": body.get("name")})
    if existing_subcategory:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Subcategory with this name already exists"})
      }
    logger.info("Creating the subcategory...")
    body_copy = body.copy()
    for key, value in body_copy.items():
      if key == 'image':
        image_data = value
        try:
          upload_response = cloudinary.uploader.upload(image_data)
          image_url = upload_response['secure_url']
          body["image_url"] = image_url
        except Exception as e:
          return {
            "statusCode": 500,
            "body": json.dumps({"message": "Failed to upload image to Cloudinary", "error": str(e)})
          }
      else:
        body[key] = value
    body.pop('image', None)

    subcategory_id = subcategories.insert_one(body).inserted_id
    logger.info(subcategory_id)
    subcategory = subcategories.find_one({"_id": subcategory_id})
    logger.info(subcategory)
    return {
      "statusCode": 200,
      "body": json.dumps(subcategory, default=json_unknown_type_handler)
    }
  except Exception as e:
    error_message = str(e)
    return {
        "statusCode": 500,
        "body": json.dumps({"errorMessage": error_message})
    }
    
def get_subcategories_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  subcategories = db.subcategories.find({})

  subcategory_list = list(subcategories)

  return {
    "statusCode": 200,
    "body": json.dumps(subcategory_list, default=json_unknown_type_handler)
  }
  
def get_subcategory_products_handler(event, context):
  try:
    logger.info("Received event: " + json.dumps(event, indent=2))

    body = json.loads(event['body'])

    subcategory_id = body.get('subcategory_id')

    if not subcategory_id:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Subcategory ID is missing in request body"})
      }

    products = db.products.find({"subcategory_id": subcategory_id})

    product_list = []
    for product in products:
      product_id = product['_id']
      variants = db.variants.find({"product_id": str(product_id)})
      product['variants'] = list(variants)
      product_list.append(product)

    if not product_list:
      return {
        "statusCode": 404,
        "body": json.dumps({"errorMessage": "No products found for the provided subcategory ID"})
      }
    else:
      return {
        "statusCode": 200,
        "body": json.dumps(product_list, default=json_unknown_type_handler)
      }
  except Exception as e:
    error_message = str(e)
    return {
      "statusCode": 500,
      "body": json.dumps({"errorMessage": error_message})
    }

def update_subcategory_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  if 'body' in event and isinstance(event['body'], str):
    body = json.loads(event['body'])
  else:
    return {
      "statusCode": 400,
      "body": json.dumps({"errorMessage": "Request body is missing or empty"})
    }
  
  is_valid, error_response = validate_schema(body, update_subcategory_schema)
  if not is_valid:
    return error_response
  
  if 'image' in body:
    encoded_image = body.get('image')
    if not encoded_image:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Image data is missing"})
      }
    decoded_image = base64.b64decode(encoded_image)
    body['image'] = decoded_image
  
  try:
    subcategory_data = body
    subcategory_id = subcategory_data.get("_id")
    if isinstance(subcategory_id, str):
      subcategory_data["_id"] = ObjectId(subcategory_id)
  except json.JSONDecodeError as e:
    return {
      "statusCode": 400,
      "body": json.dumps({"message": "Invalid JSON format in request body"})
    }
    
  existing_subcategory = db.subcategories.find_one({"name": subcategory_data.get("name"), "_id": {"$ne": subcategory_data.get("_id")}})
  if existing_subcategory:
    return {
      "statusCode": 400,
      "body": json.dumps({"errorMessage": "Subcategory with this name already exists"})
    }

  subcategory_data_copy = subcategory_data.copy()
  for key, value in subcategory_data_copy.items():
    if key == 'image':
      image_data = value
      try:
        upload_response = cloudinary.uploader.upload(image_data)
        image_url = upload_response['secure_url']
        subcategory_data["image_url"] = image_url
      except Exception as e:
        return {
          "statusCode": 500,
          "body": json.dumps({"message": "Failed to upload image to Cloudinary", "error": str(e)})
        }
    else:
      subcategory_data[key] = value

  subcategory_data.pop('image', None)
  
  logger.info("Updating the subcategory...")
  
  updated_subcategory = db.subcategories.find_one_and_update({"_id": subcategory_data["_id"]}, {"$set": subcategory_data}, return_document=True)
  if not updated_subcategory:
    return {
      "statusCode": 404,
      "body": json.dumps({"message": "Category not found or not updated"})
    }
  else:
    updated_subcategory["_id"] = str(updated_subcategory["_id"])
    return {
      "statusCode": 200,
      "body": json.dumps({"message": "Category updated successfully", "category": updated_subcategory})
    }
    
def delete_subcategory_handler(event, context):
  try:
    subcategory_id = event.get('pathParameters', {}).get('subcategory_id')

    if not subcategory_id:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Subcategory ID is missing in the request"})
      }

    subcategory_id = ObjectId(subcategory_id)

    subcategories = db.subcategories

    existing_subcategory = subcategories.find_one({"_id": subcategory_id})
    if not existing_subcategory:
      return {
        "statusCode": 404,
        "body": json.dumps({"errorMessage": "Subcategory not found"})
      }

    subcategories.delete_one({"_id": subcategory_id})

    return {
      "statusCode": 200,
      "body": json.dumps({"message": "Subcategory deleted successfully"})
    }
  except Exception as e:
    error_message = str(e)
    return {
      "statusCode": 500,
      "body": json.dumps({"errorMessage": error_message})
    }
    
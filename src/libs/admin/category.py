from io import BytesIO
import logging
import json
import cloudinary.uploader
import base64
from bson import ObjectId
from werkzeug.formparser import parse_form_data
from werkzeug.datastructures import MultiDict

from libs.utils import (
  json_unknown_type_handler, 
  validate_schema
)
from config.db import db
from config.schemas import (
  category_schema, 
  update_category_schema
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# def category_handler(event, context):
#   try:
#     logger.info("Received event: " + json.dumps(event, indent=2))
    
#     event_body_bytes = BytesIO(event['body'])
#     form_data = MultiDict()
#     parse_form_data(event_body_bytes, form_data)
    
#     if 'name' not in form_data or 'image' not in form_data:
#       return {
#         "statusCode": 400,
#         "body": json.dumps({"errorMessage": "Required form fields are missing"})
#       }
#     is_valid, error_response = validate_schema(form_data, category_schema)
#     if not is_valid:
#       return error_response
      
#     name = form_data.get('name')
#     image = form_data.get('image')
#     # decoded_image = base64.b64decode(encoded_image)
      
#     logger.info("Initializing the collection")
#     categories = db.categories
    
#     existing_category = categories.find_one({"name": name})
#     if existing_category:
#       return {
#         "statusCode": 400,
#         "body": json.dumps({"errorMessage": "Category with this name already exists"})
#       }
#     try:
#       upload_response = cloudinary.uploader.upload(image)
#       image_url = upload_response['secure_url']
#     except Exception as e:
#       return {
#         "statusCode": 500,
#         "body": json.dumps({"message": "Failed to upload image to Cloudinary", "error": str(e)})
#       }
    
#     category = {
#       "name": name,
#       "image_url": image_url
#     }

#     logger.info("Creating the category...")
#     category_id = categories.insert_one(category).inserted_id
#     logger.info(category_id)
#     category = categories.find_one({"_id": category_id})
#     logger.info(category)
#     return {
#       "statusCode": 200,
#       "body": json.dumps(category, default=json_unknown_type_handler)
#     }
#   except Exception as e:
#     error_message = str(e)
#     return {
#         "statusCode": 500,
#         "body": json.dumps({"errorMessage": error_message})
#     }

def category_handler(event, context):
  try:
    if 'body' in event and isinstance(event['body'], str):
      body = json.loads(event['body'])
    else:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Request body is missing or empty"})
      }
    
    is_valid, error_response = validate_schema(body, category_schema)
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
    categories = db.categories
    
    existing_category = categories.find_one({"name": body.get("name")})
    if existing_category:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Category with this name already exists"})
      }
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

    logger.info("Creating the category...")
    category_id = categories.insert_one(body).inserted_id
    logger.info(category_id)
    category = categories.find_one({"_id": category_id})
    logger.info(category)
    return {
      "statusCode": 200,
      "body": json.dumps(category, default=json_unknown_type_handler)
    }
  except Exception as e:
    error_message = str(e)
    return {
        "statusCode": 500,
        "body": json.dumps({"errorMessage": error_message})
    }
    
def get_categories_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  categories = db.categories.find({})

  category_list = list(categories)

  return {
    "statusCode": 200,
    "body": json.dumps(category_list, default=json_unknown_type_handler)
  }

def get_category_subcategories_handler(event, context):
  try:
    logger.info("Received event: " + json.dumps(event, indent=2))

    body = json.loads(event['body'])

    category_id = body.get('category_id')

    if not category_id:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Category ID is missing in request body"})
      }

    subcategories = db.subcategories.find({"category_id": category_id})

    subcategory_list = list(subcategories)

    if not subcategory_list:
      return {
          "statusCode": 404,
          "body": json.dumps({"errorMessage": "No subcategories found for the provided category ID"})
      }
    else:
      return {
        "statusCode": 200,
        "body": json.dumps(subcategory_list, default=json_unknown_type_handler)
      }
  except Exception as e:
    error_message = str(e)
    return {
      "statusCode": 500,
      "body": json.dumps({"errorMessage": error_message})
    }

def update_category_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  if 'body' in event and isinstance(event['body'], str):
    body = json.loads(event['body'])
  else:
    return {
      "statusCode": 400,
      "body": json.dumps({"errorMessage": "Request body is missing or empty"})
    }
  
  is_valid, error_response = validate_schema(body, update_category_schema)
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
    category_data = body
    category_id = category_data.get("_id")
    if isinstance(category_id, str):
      category_data["_id"] = ObjectId(category_id)
  except json.JSONDecodeError as e:
    return {
      "statusCode": 400,
      "body": json.dumps({"message": "Invalid JSON format in request body"})
    }
  
  existing_category = db.categories.find_one({"name": category_data.get("name"), "_id": {"$ne": category_data.get("_id")}})
  if existing_category:
    return {
      "statusCode": 400,
      "body": json.dumps({"errorMessage": "Category with this name already exists"})
    }
    
  category_data_copy = category_data.copy()
  for key, value in category_data_copy.items():
    if key == 'image':
      image_data = value
      try:
        upload_response = cloudinary.uploader.upload(image_data)
        image_url = upload_response['secure_url']
        category_data["image_url"] = image_url
      except Exception as e:
        return {
          "statusCode": 500,
          "body": json.dumps({"message": "Failed to upload image to Cloudinary", "error": str(e)})
        }
    else:
      category_data[key] = value
  
  category_data.pop('image', None)

  logger.info("Updating the category...")
  updated_category = db.categories.find_one_and_update({"_id": category_data["_id"]}, {"$set": category_data}, return_document=True)
  if not updated_category:
    return {
      "statusCode": 404,
      "body": json.dumps({"message": "Category not found or not updated"})
    }
  else:
    updated_category["_id"] = str(updated_category["_id"])
    return {
      "statusCode": 200,
      "body": json.dumps({"message": "Category updated successfully", "category": updated_category})
    }

def delete_category_handler(event, context):
  try:
    category_id = event.get('pathParameters', {}).get('category_id')

    if not category_id:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Category ID is missing in the request"})
      }

    category_id = ObjectId(category_id)

    categories = db.categories

    existing_category = categories.find_one({"_id": category_id})
    if not existing_category:
      return {
        "statusCode": 404,
        "body": json.dumps({"errorMessage": "Category not found"})
      }

    categories.delete_one({"_id": category_id})

    return {
      "statusCode": 200,
      "body": json.dumps({"message": "Category deleted successfully"})
    }
  except Exception as e:
    error_message = str(e)
    return {
      "statusCode": 500,
      "body": json.dumps({"errorMessage": error_message})
    }
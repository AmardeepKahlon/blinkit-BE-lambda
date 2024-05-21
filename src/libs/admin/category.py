from io import BytesIO
import logging
import json
import cloudinary.uploader
import base64
import cgi
from bson import ObjectId
from urllib.parse import parse_qs
from multipart import MultipartParser,MultipartError

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

# def category_formdata_handler(event, context):
#     print("Received event:", json.dumps(event, indent=2))

#     # Example handling for REST API Gateway
#     if event.get('httpMethod') == 'POST' and event.get('body'):
#         body = event['body']
#         try:
#             body = json.loads(body)
#             name = body.get('name', '')
#             email = body.get('email', '')
#             print("Received body:", json.dumps(body, indent=2))
            
#         except json.JSONDecodeError:
#             name = ''
#             email = ''
#     else:
#         name = ''
#         email = ''

#     # Create a response
#     response = {
#         "statusCode": 200,
#         "headers": {
#             "Content-Type": "application/json"
#         },
#         "body": json.dumps({
#             "message": f"Received name: {name}, email: {email}"
#         })
#     }

#     return response
def category_formdata_handler(event, context):
    logger.info("Received event: %s", json.dumps(event, indent=2))

    name = ''
    email = ''

    if event.get('httpMethod') == 'POST':
        content_type = event['headers'].get('Content-Type', event['headers'].get('content-type'))
        
        if content_type and 'multipart/form-data' in content_type:
            body = event['body']
            
            # if event['isBase64Encoded']:
            #     # Decode body from base64
            #     body = base64.b64decode(body)
            
            try:
                # Extract boundary
                # boundary = None
                # parts = content_type.split("boundary=")
                # if len(parts) > 1:
                #     boundary = parts[1]
                
                # if boundary is None:
                #     raise ValueError("Missing boundary in Content-Type header")
                
                # Create a fake environment
                environ = {
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': content_type,
                    'CONTENT_LENGTH': len(body)
                }
                
                # Parse the multipart form data
                fp = BytesIO(body.encode())
                form = cgi.FieldStorage(fp=fp, environ=environ, keep_blank_values=True)
                if 'name' in form:
                    name = form['name'].value
                if 'email' in form:
                    email = form['email'].value

                logger.info("Parsed name: %s, email: %s", name, email)
            except Exception as e:
                logger.error("Failed to parse multipart data: %s", str(e))
        else:
            logger.warning("Unsupported or missing Content-Type: %s", content_type)

    response = {
      "statusCode": 200,
      "headers": {
          "Content-Type": "application/json"
      },
      "body": json.dumps({
          "message": f"Received name: {name}, email: {email}"
      })
    }

    return response

# def category_formdata_handler(event, context):
    logger.info("Received event: %s", json.dumps(event, indent=2))

    name = ''
    email = ''

    if event.get('httpMethod') == 'POST':
        content_type = event['headers'].get('Content-Type', event['headers'].get('content-type'))
        
        if content_type and 'multipart/form-data' in content_type:
            body = event['body']
            
            
            if event['isBase64Encoded']:
                body = base64.b64decode(body)
                print('body-------------------->',body )
            
            try:
                # Create a fake environment
                environ = {
                    'REQUEST_METHOD': 'POST',
                    'CONTENT_TYPE': content_type,
                    'CONTENT_LENGTH': len(body)
                }
                
                # Parse the multipart form data
                fp = BytesIO(body)
                form = cgi.FieldStorage(fp=fp, environ=environ, keep_blank_values=True)

                if 'name' in form:
                    name = form['name'].value
                if 'email' in form:
                    email = form['email'].value

                print("Parsed name------------------: %s, email----------: %s", name, email)
            except Exception as e:
                logger.error("Failed to parse multipart data: %s", str(e))
        else:
            logger.warning("Unsupported Content-Type: %s", content_type)

    response = {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "message": f"Received name: {name}, email: {email}"
        })
    }

    return response
# def category_formdata_handler(event, context):
#   parser = StreamingFormDataParser(headers=event['params']['header'])
#     # As the form has 2 fields: 1x Text & 1x File. 
#     # Here we initiate two ValueTarget to hold values in memory.
# try:
#   if body in event:
#         category_name = ValueTarget() 
#         image = ValueTarget()
#         parser.register("name", category_name)
#         parser.register("image", image)
#         mydata = base64.b64decode(event["body"])
#         parser.data_received(mydata)
#         logger.info(mydata,'------------------>here is my data')
#         return {
#          "statusCode": 200,
#          "body": json.dumps(category, default=json_unknown_type_handler)
#           }
# except Exception as e:
#     error_message = str(e)
#     return {
#         "statusCode": 500,
#         "body": json.dumps({"errorMessage": "galat ho raha hai chacha"})
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
    print(body,'----------------------------------->')

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
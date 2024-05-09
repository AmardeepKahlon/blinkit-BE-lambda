import logging
import json
import os
import cloudinary
import cloudinary.uploader
import base64

from bson import ObjectId
from jose import jwt
from multipart import parse_form_data

from utils import (
  secret_key, 
  hash_password, 
  token_required, 
  json_unknown_type_handler, 
  validate_schema, 
  verify_password
)
from db import db
from schemas import (
  user_schema, 
  admin_schema, 
  category_schema, 
  subcategory_schema, 
  product_schema, 
  product_variant_schema, 
  update_category_schema, 
  update_subcategory_schema, 
  update_product_schema
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
  logger.info("Received event: " + json.dumps(event, indent=2))
  
  try:
      body = json.loads(event.get("body", "{}"))
  except json.JSONDecodeError:
    return {
      "statusCode": 400,
      "body": json.dumps({"message": "Invalid JSON format in request body"})
    }
    
  email = body.get("email", None)
  password = body.get("password", None)
  
  logger.info("Processing login...")
  if not email or not password:
    return {
      "statusCode": 401,
      "body": json.dumps({"message": "Invalid email or password"})
    }

  user_data = db.blinkit_users.find_one({"email": email})
  if user_data and verify_password(password, user_data.get("password")):
    token = jwt.encode({"email": email, "role": user_data.get("role", "USER")}, secret_key, algorithm="HS256")
    return {
      "statusCode": 200,
      "body": json.dumps({"token": token, "role": user_data.get("role", "USER"), "user_name": user_data.get("fullname"), "user_email": user_data.get("email")})
    }

  return {
      "statusCode": 401,
      "body": json.dumps({"message": "Invalid email or password"})
  }

# @token_required
def user_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))
  
  # if not is_admin(event):
  #   return {
  #     "statusCode": 403,
  #     "body": json.dumps({"message": "Unauthorized"})
  #   }
  
  logger.info("initializing the collection")
  users = db.blinkit_users
  
  logger.info("creating the user...")
  body = event.get("body", None)
  if body is None:
    return {
      "statusCode": 400,
      "body": json.dumps({"message": "Missing request body"})
    }
  try:
    user_data = json.loads(body)
    existing_user = users.find_one({"email": user_data.get("email")})
    if existing_user:
      return {
        "statusCode": 409,
        "body": json.dumps({"message": "User with this email already exists"})
      }
    user_data["role"] = "USER"
    user_data["password"] = hash_password(user_data.get("password"))
  except json.JSONDecodeError as e:
    return {
      "statusCode": 400,
      "body": json.dumps({"message": "Invalid JSON format in request body"})
    }
  is_valid, error_response = validate_schema(user_data, user_schema)
  if not is_valid:
    return error_response
  user_id = users.insert_one(user_data).inserted_id
  logger.info(user_id)
  user = users.find_one({"_id": user_id}, {"password": False})
  logger.info(user)
  return {
    "statusCode": 200,
    "body": json.dumps(user, default=json_unknown_type_handler)
  }

# @token_required
def admin_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  logger.info("initializing the collection")
  admins = db.blinkit_users
  
  logger.info("creating the admin...")
  body = event.get("body", None)
  if body is None:
    return {
      "statusCode": 400,
      "body": json.dumps({"message": "Missing request body"})
    }
  
  try:
    admin_data = json.loads(body)
    admin_data["role"] = "ADMIN"
    admin_data["password"] = hash_password(admin_data.get("password"))
  except json.JSONDecodeError as e:
    return {
        "statusCode": 400,
        "body": json.dumps({"message": "Invalid JSON format in request body"})
    }

  is_valid, error_response = validate_schema(admin_data, admin_schema)
  if not is_valid:
    return error_response
  admin_id = admins.insert_one(admin_data).inserted_id
  logger.info(admin_id)
  admin = admins.find_one({"_id": admin_id}, {"password": False})
  logger.info(admin)
  return {
    "statusCode": 200,
    "body": json.dumps(admin, default=json_unknown_type_handler)
  }

# @token_required
# async def invoke_category_handler(event, context):
#   result = await category_handler(event, context)
#   return result

@token_required
def category_handler(event, context):
  # print("context=====>",context,event)
  try:
    if 'body' in event and isinstance(event['body'], str):
      body = json.loads(event['body'])
    else:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Request body is missing or empty"})
      }
    
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
    logger.info("Creating the category...")
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

    is_valid, error_response = validate_schema(body, category_schema)
    if not is_valid:
      return error_response

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

@token_required
def subcategory_handler(event, context):
  try:
    if 'body' in event and isinstance(event['body'], str):
      body = json.loads(event['body'])
    else:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Request body is missing or empty"})
      }
    
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
    
    is_valid, error_response = validate_schema(body, subcategory_schema)
    if not is_valid:
      return error_response

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

@token_required
def product_handler(event, context):
  try:
    if 'body' in event and isinstance(event['body'], str):
      body = json.loads(event['body'])
      variants_body = body.get('variants')
      if variants_body is None:
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Variants are missing in the request body"})
        }
    else:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Request body is missing or empty"})
      }
      
    if 'body' in event and isinstance(event['body'], str):
      body = json.loads(event['body'])
    else:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Request body is missing or empty"})
      }
    
    encoded_image = body.get('image')
    if not encoded_image:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Product Image data is missing"})
      }
    decoded_image = base64.b64decode(encoded_image)
    body['image'] = decoded_image
    
    encoded_images = variants_body.get('images')
    if not encoded_images:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Variant Image data is missing"})
      }
    if not isinstance(encoded_images, list):
      encoded_images_list = [encoded_images]
    
    if len(encoded_images_list) < 1:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "At least one image is required"})
      }
    
    if len(encoded_images_list) > 5:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Maximum 5 images are allowed"})
      }
    
    decoded_images = [base64.b64decode(image) for image in encoded_images_list]
    image_urls = []
    logger.info("Received event: " + json.dumps(event, indent=2))

    logger.info("Initializing the collections...")
    products = db.products
    variants = db.variants
    
    logger.info("Creating the product...")
    try:
      product_image_data = body.get('image')
      product_upload_response = cloudinary.uploader.upload(product_image_data)
      product_image_url = product_upload_response['secure_url']
    except Exception as e:
      return {
        "statusCode": 500,
        "body": json.dumps({"message": "Failed to upload image to Cloudinary", "error": str(e)})
      }
    for image_data in decoded_images:
      try:
        upload_response = cloudinary.uploader.upload(image_data)
        image_url = upload_response['secure_url']
        image_urls.append(image_url)
      except Exception as e:
        return {
          "statusCode": 500,
          "body": json.dumps({"message": "Failed to upload image to Cloudinary", "error": str(e)})
        }
        
    body['image_url'] = product_image_url
    variants_body['image_urls'] = image_urls
    body.pop('image', None)
    body.pop('variants', None)
    variants_body.pop('images', None)
    
    is_valid, error_response = validate_schema(body, product_schema)
    if not is_valid:
      return error_response
    is_valid, error_response = validate_schema(variants_body, product_variant_schema)
    if not is_valid:
      return error_response

    product_id = products.insert_one(body).inserted_id
    logger.info(product_id)
    product = products.find_one({"_id": product_id})
    logger.info(product)
    variant_id = variants.insert_one(variants_body).inserted_id
    logger.info(variant_id)
    variant = variants.find_one({"_id": variant_id})
    logger.info(variant)
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

@token_required
def get_categories_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  categories = db.categories.find({})

  category_list = list(categories)

  return {
    "statusCode": 200,
    "body": json.dumps(category_list, default=json_unknown_type_handler)
  }

@token_required
def update_category_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  body = event.get("body", None)
  if body is None:
    return {
      "statusCode": 400,
      "body": json.dumps({"message": "Missing request body"})
    }
  
  is_valid, error_response = validate_schema(body, update_category_schema)
  if not is_valid:
    return error_response
  
  logger.info("Updating the category...")
  try:
    category_data = json.loads(body)
    category_id = category_data.get("_id")
    if isinstance(category_id, str):
      category_data["_id"] = ObjectId(category_id)
  except json.JSONDecodeError as e:
    return {
      "statusCode": 400,
      "body": json.dumps({"message": "Invalid JSON format in request body"})
    }

  updated_category = db.categories.update_one({"_id": category_data["_id"]}, {"$set": category_data})
  if updated_category.modified_count == 0:
    return {
      "statusCode": 404,
      "body": json.dumps({"message": "Category not found"})
    }
  else:
    return {
      "statusCode": 200,
      "body": json.dumps({"message": "Category updated successfully"})
    }

@token_required
def get_subcategories_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  subcategories = db.subcategories.find({})

  subcategory_list = list(subcategories)

  return {
    "statusCode": 200,
    "body": json.dumps(subcategory_list, default=json_unknown_type_handler)
  }

@token_required
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

@token_required
def update_subcategory_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  body = event.get("body", None)
  if body is None:
    return {
      "statusCode": 400,
      "body": json.dumps({"message": "Missing request body"})
    }
  
  is_valid, error_response = validate_schema(body, update_subcategory_schema)
  if not is_valid:
    return error_response
  
  logger.info("Updating the subcategory...")
  try:
    subcategory_data = json.loads(body)
    subcategory_id = subcategory_data.get("_id")
    if isinstance(subcategory_id, str):
      subcategory_data["_id"] = ObjectId(subcategory_id)
  except json.JSONDecodeError as e:
    return {
      "statusCode": 400,
      "body": json.dumps({"message": "Invalid JSON format in request body"})
    }

  updated_subcategory = db.subcategories.update_one({"_id": subcategory_data["_id"]}, {"$set": subcategory_data})
  
  if updated_subcategory.modified_count == 0:
    return {
      "statusCode": 404,
      "body": json.dumps({"message": "Category not found"})
    }
  else:
    return {
      "statusCode": 200,
      "body": json.dumps({"message": "Category updated successfully"})
    }

@token_required
def get_products_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  products = db.products.find({})

  product_list = list(products)

  return {
    "statusCode": 200,
    "body": json.dumps(product_list, default=json_unknown_type_handler)
  }

@token_required
def get_specific_product_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  product_id = event.get("pathParameters", {}).get("product_id")
  if not product_id:
    return {
      "statusCode": 400,
      "body": json.dumps({"message": "Product ID is required"})
    }
  if isinstance(product_id, str):
    product = db.products.find_one({"_id": ObjectId(product_id)})

  if not product:
    return {
      "statusCode": 404,
      "body": json.dumps({"message": "Product not found"})
    }

  return {
    "statusCode": 200,
    "body": json.dumps(product, default=json_unknown_type_handler)
  }

@token_required
def update_product_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  body = event.get("body", None)
  if body is None:
    return {
      "statusCode": 400,
      "body": json.dumps({"message": "Missing request body"})
    }
  
  is_valid, error_response = validate_schema(body, update_product_schema)
  if not is_valid:
    return error_response
  
  logger.info("Updating the product...")
  try:
    product_data = json.loads(body)
    product_id = product_data.get("_id")
    if isinstance(product_id, str):
      product_data["_id"] = ObjectId(product_id)
  except json.JSONDecodeError as e:
    return {
      "statusCode": 400,
      "body": json.dumps({"message": "Invalid JSON format in request body"})
    }

  update_product = db.products.update_one({"_id": product_data["_id"]}, {"$set": product_data})
  
  if update_product.modified_count == 0:
    return {
      "statusCode": 404,
      "body": json.dumps({"message": "Category not found"})
    }
  else:
    return {
      "statusCode": 200,
      "body": json.dumps({"message": "Category updated successfully"})
    }

# def admin_login_handler(event, context):
#   logger.info("Received event: " + json.dumps(event, indent=2))
  
#   try:
#     body = json.loads(event.get("body", "{}"))
#   except json.JSONDecodeError:
#     return {
#       "statusCode": 400,
#       "body": json.dumps({"message": "Invalid JSON format in request body"})
#     }
  
#   username = body.get("username", None)
#   password = body.get("password", None)
  
#   logger.info("processing login...")
#   if not username or not password:
#     return {
#       "statusCode": 401,
#       "body": json.dumps({"message": "Invalid username or password"})
#     }

#   admin_data = db.blinkit_admins.find_one({"username": username})
#   if admin_data and verify_password(password, admin_data.get("password")):
#     token = jwt.encode({"username": username, "role": admin_data.get("role", "ADMIN")}, secret_key, algorithm="HS256")
#     return {
#       "statusCode": 200,
#       "body": json.dumps({"token": token})
#     }

#   return {
#     "statusCode": 401,
#     "body": json.dumps({"message": "Invalid username or password"})
#   }

import logging
import json

from libs.utils import (
  hash_password, 
  json_unknown_type_handler, 
  validate_schema
)
from config.db import db
from config.schemas import (
  admin_schema
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
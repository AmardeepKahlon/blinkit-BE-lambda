import logging
import json


from libs.utils import (
  hash_password, 
  json_unknown_type_handler, 
  validate_schema
)
from config.db import db
from config.schemas import (
  user_schema
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


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
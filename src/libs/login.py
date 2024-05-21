import logging
import json

from jose import jwt

from libs.utils import (
  secret_key, 
  verify_password
)
from config.db import db

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def login_handler(event, context):
  logger.info(f"Received event: {json.dumps(event, indent=2)}")

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
import os
import bson
import json
from dotenv import load_dotenv
from functools import wraps
from jose import jwt
from jsonschema import validate, ValidationError
import bcrypt

load_dotenv()

secret_key = os.environ['SECRET_KEY']

def hash_password(password):
  salt = bcrypt.gensalt()
  hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
  return hashed_password

def verify_password(password, hashed_password):
  return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def validate_schema(data, schema):
  try:
    validate(instance=data, schema=schema)
  except ValidationError as e:
    return False, {"statusCode": 400, "body": json.dumps({"message": str(e)})}
  return True, None

def token_required(func):
  @wraps(func)
  def wrapper(event, context):
    # print("event======>",event['body'])
    is_valid, payload = verify_token(event)
    if not is_valid:
      return payload
    return func(event, context, payload)
  return wrapper

def token_required_is_admin(func):
  @wraps(func)
  def wrapper(event, context):
    # print("event======>",event['body'])
    is_valid, payload = verify_token_is_admin(event)
    if not is_valid:
      return payload
    return func(event, context)
  return wrapper

def verify_token(event):
  auth_header = event.get('headers', {}).get('Authorization')

  if not auth_header:
    return False, {"statusCode": 401, "body": json.dumps({"message": "Missing token"})}

  parts = auth_header.split()
  if len(parts) != 2 or parts[0].lower() != 'bearer':
    return False, {"statusCode": 401, "body": json.dumps({"message": "Invalid token format"})}

  token = parts[1]
  
  try:
    payload = jwt.decode(token, secret_key, algorithms=['HS256'])
    if payload.get('role') != 'USER':
      return False, {"statusCode": 403, "body": json.dumps({"message": "Not authorized. User role required"})}
    return True, payload
  except jwt.ExpiredSignatureError:
    return False, {"statusCode": 401, "body": json.dumps({"message": "Token expired"})}
  except jwt.JWTError:
    return False, {"statusCode": 401, "body": json.dumps({"message": "Invalid token"})}
  
def verify_token_is_admin(event):
  auth_header = event.get('headers', {}).get('Authorization')

  if not auth_header:
    return False, {"statusCode": 401, "body": json.dumps({"message": "Missing token"})}

  parts = auth_header.split()
  if len(parts) != 2 or parts[0].lower() != 'bearer':
    return False, {"statusCode": 401, "body": json.dumps({"message": "Invalid token format"})}

  token = parts[1]
  
  try:
    payload = jwt.decode(token, secret_key, algorithms=['HS256'])
    if payload.get('role') != 'ADMIN':
      return False, {"statusCode": 403, "body": json.dumps({"message": "Not authorized. Admin role required"})}
    return True, payload
  except jwt.ExpiredSignatureError:
    return False, {"statusCode": 401, "body": json.dumps({"message": "Token expired"})}
  except jwt.JWTError:
    return False, {"statusCode": 401, "body": json.dumps({"message": "Invalid token"})}

def json_unknown_type_handler(x):
  """
  JSON cannot serialize decimal, datetime and ObjectId. So we provide this handler.
  """
  if isinstance(x, bson.ObjectId):
    return str(x)
  raise TypeError("Unknown datetime type")
  
# def is_admin(event):
#   is_valid, payload = verify_token(event)

#   if not is_valid:
#     return False

#   roles = payload.get('role', [])
#   return 'admin' in roles
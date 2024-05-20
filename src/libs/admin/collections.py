import json
import logging
from bson import ObjectId
from pymongo import MongoClient

from config.db import db

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_creation_collection():
  return db.creation
def ensure_creation_collection():
  collection = get_creation_collection()
  # Create any required indexes here, for example:
  # collection.create_index([("field_name", pymongo.ASCENDING)], unique=True)
  logger.info("Ensured creation collection exists.")

def create_creation(event, context):
  try:
    logger.info(f"Received event: {json.dumps(event, indent=2)}")

    if 'body' not in event or not isinstance(event['body'], str):
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Request body is missing or empty"})
        }

    creation_data = json.loads(event['body'])
    collection = get_creation_collection()
    
    result = collection.insert_one(creation_data)
    logger.info(f"Creation document inserted with ID: {result.inserted_id}")

    return {
      'statusCode': 200,
      'body': json.dumps({'creationId': str(result.inserted_id)})
    }
  except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
    return {
      'statusCode': 500,
      'body': json.dumps({'errorMessage': str(e)})
    }
      
def read_creation(event, context):
  try:
    creation_id = event['pathParameters']['id']
    collection = get_creation_collection()

    if document := collection.find_one({"_id": ObjectId(creation_id)}):
      return {
        'statusCode': 200,
        'body': json.dumps(document, default=str)  # Convert ObjectId to str
      }
    else:
      return {
        'statusCode': 404,
        'body': json.dumps({"errorMessage": "Document not found"})
      }
  except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
    return {
      'statusCode': 500,
      'body': json.dumps({'errorMessage': str(e)})
    }
def update_creation(event, context):
  try:
    creation_id = event['pathParameters']['id']
    if 'body' not in event or not isinstance(event['body'], str):
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Request body is missing or empty"})
      }

    update_data = json.loads(event['body'])
    collection = get_creation_collection()
    
    result = collection.update_one({"_id": ObjectId(creation_id)}, {"$set": update_data})
    if result.matched_count:
      return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Document updated successfully'})
      }
    else:
      return {
        'statusCode': 404,
        'body': json.dumps({"errorMessage": "Document not found"})
      }
  except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
    return {
      'statusCode': 500,
      'body': json.dumps({'errorMessage': str(e)})
    }
      
def delete_creation(event, context):
  try:
    creation_id = event['pathParameters']['id']
    collection = get_creation_collection()
    
    result = collection.delete_one({"_id": ObjectId(creation_id)})
    if result.deleted_count:
      return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Document deleted successfully'})
      }
    else:
      return {
        'statusCode': 404,
        'body': json.dumps({"errorMessage": "Document not found"})
      }
  except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
    return {
      'statusCode': 500,
      'body': json.dumps({'errorMessage': str(e)})
    }

import json
import logging
from bson import ObjectId

from config.db import db
from libs.utils import validate_schema
from config.schemas import collection_schema, update_collection_schema

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def create_collection(event, context):
  try:
    logger.info(f"Received event: {json.dumps(event, indent=2)}")

    if 'body' not in event or not isinstance(event['body'], str):
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Request body is missing or empty"})
        }
    collection_data = json.loads(event['body'])
    
    is_valid, error_response = validate_schema(collection_data, collection_schema)
    if not is_valid:
      return error_response
    
    logger.info("Initializing the collections...")
    collection = db.collections
    
    if existing_collection := collection.find_one({"collection_name": collection_data.get("collection_name")}):
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Collection with this name already exists"})
      }
    
    result = collection.insert_one(collection_data)
    logger.info(f"Collection document inserted with ID: {result.inserted_id}")

    return {
      'statusCode': 200,
      'body': json.dumps({'message': 'Document created successfully'})
    }
  except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
    return {
      'statusCode': 500,
      'body': json.dumps({'errorMessage': str(e)})
    }
      
def get_collection(event, context):
  try:
    logger.info(f"Received event: {json.dumps(event, indent=2)}")
    collection_id = event['pathParameters']['collection_id']
    
    logger.info("Initializing the collections...")
    collection = db.collections

    if document := collection.find_one({"_id": ObjectId(collection_id)}):
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
    
def get_collections(event, context):
  try:
    logger.info(f"Received event: {json.dumps(event, indent=2)}")

    logger.info("Initializing the collections...")
    collection = db.collections

    if documents := list(collection.find({})):
      return {
        'statusCode': 200,
        'body': json.dumps(documents, default=str)
      }
    else:
      return {
        'statusCode': 404,
        'body': json.dumps({"errorMessage": "No collections found"})
      }
  except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
    return {
      'statusCode': 500,
      'body': json.dumps({'errorMessage': str(e)})
    }

def update_collection(event, context):
  try:
    logger.info(f"Received event: {json.dumps(event, indent=2)}")
    
    if 'body' not in event or not isinstance(event['body'], str):
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Request body is missing or empty"})
      }

    update_data = json.loads(event['body'])
    
    is_valid, error_response = validate_schema(update_data, update_collection_schema)
    if not is_valid:
      return error_response
    
    logger.info("Initializing the collections...")
    collection = db.collections
    
    if update_data['collection_name']:
      if existing_collection := collection.find_one({"collection_name": update_data.get("collection_name")}):
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Collection with this name already exists"})
        }
    
    collection_id = update_data['_id']
    update_data.pop('_id', None)
    result = collection.update_one({"_id": ObjectId(collection_id)}, {"$set": update_data})
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
      
def delete_collection(event, context):
  try:
    logger.info(f"Received event: {json.dumps(event, indent=2)}")
    
    collection_id = event['pathParameters']['collection_id']
    
    logger.info("Initializing the collections...")
    collection = db.collections
    
    result = collection.delete_one({"_id": ObjectId(collection_id)})
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

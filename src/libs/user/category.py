import logging
import json

from libs.utils import (
  json_unknown_type_handler
)
from config.db import db

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
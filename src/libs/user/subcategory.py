import logging
import json


from libs.utils import (
  json_unknown_type_handler
)
from config.db import db

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_subcategories_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  subcategories = db.subcategories.find({})

  subcategory_list = list(subcategories)

  return {
    "statusCode": 200,
    "body": json.dumps(subcategory_list, default=json_unknown_type_handler)
  }
  
def get_subcategory_products_handler(event, context):
  try:
    logger.info("Received event: " + json.dumps(event, indent=2))

    body = json.loads(event['body'])

    subcategory_id = body.get('subcategory_id')

    if not subcategory_id:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Subcategory ID is missing in request body"})
      }

    products = db.products.find({"subcategory_id": subcategory_id})

    product_list = []
    for product in products:
      product_id = product['_id']
      variants = db.variants.find({"product_id": str(product_id)})
      product['variants'] = list(variants)
      product_list.append(product)

    if not product_list:
      return {
        "statusCode": 404,
        "body": json.dumps({"errorMessage": "No products found for the provided subcategory ID"})
      }
    else:
      return {
        "statusCode": 200,
        "body": json.dumps(product_list, default=json_unknown_type_handler)
      }
  except Exception as e:
    error_message = str(e)
    return {
      "statusCode": 500,
      "body": json.dumps({"errorMessage": error_message})
    }
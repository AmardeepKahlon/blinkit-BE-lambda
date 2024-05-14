import logging
import json

from bson import ObjectId

from libs.utils import (
  json_unknown_type_handler
)
from config.db import db

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_products_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  products = db.products.find({})

  product_list = []
  for product in products:
    product_id = product['_id']
    variants = db.variants.find({"product_id": str(product_id)})
    product['variants'] = list(variants)
    product_list.append(product)

  return {
    "statusCode": 200,
    "body": json.dumps(product_list, default=json_unknown_type_handler)
  }
  
def get_specific_product_handler(event, context):
  logger.info("Received event: " + json.dumps(event, indent=2))

  product_id = event.get("pathParameters", {}).get("product_id")
  if not product_id:
    return {
      "statusCode": 400,
      "body": json.dumps({"message": "Product ID is required"})
    }

  product = db.products.find_one({"_id": ObjectId(product_id)})
  if not product:
    return {
      "statusCode": 404,
      "body": json.dumps({"message": "Product not found"})
    }

  variants = db.variants.find({"product_id": str(product_id)})
  product['variants'] = list(variants)

  return {
    "statusCode": 200,
    "body": json.dumps(product, default=json_unknown_type_handler)
  }
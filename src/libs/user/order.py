import datetime
import json
import logging
import os
from jose import jwt
from bson import ObjectId

from libs.utils import (
  json_unknown_type_handler, 
  validate_schema
)
from config.db import db
from config.schemas import order_schema

logger = logging.getLogger()
logger.setLevel(logging.INFO)
secret_key = os.environ['SECRET_KEY']
def order_handler(event, context, payload):
  try:
    logger.info(f"Received event: {json.dumps(event, indent=2)}")

    if 'body' not in event or not isinstance(event['body'], str):
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Request body is missing or empty"})
      }

    order_data = json.loads(event['body'])
    is_valid, error_response = validate_schema(order_data, order_schema)
    if not is_valid:
      return error_response
    order_items = order_data.get('order_items', [])
    if not order_items:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Order items are missing or empty"})
      }
    user_email = payload.get('email')
    payment_mode = order_data.get('paymentMode', 'Paid Online')
    delivery_charges = order_data.get('delivery_charges', 0)
    handling_charges = order_data.get('handling_charges', 0)
    delivery_address = order_data.get('delivery_address')
    product_details = []
    total_quantity = 0
    for order_item in order_items:
      product_id = order_item.get('product_id')
      variant_id = order_item.get('variant_id')
      quantity = int(order_item.get('quantity'))
      total_quantity += quantity

      product = db.products.find_one({"_id": ObjectId(product_id)})
      if not product:
        logger.error(f"Product not found for order item: {order_item}")
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Product not found"})
        }

      variant = db.variants.find_one({"_id": ObjectId(variant_id)})
      if not variant:
        logger.error(f"Variant not found for order item: {order_item}")
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Variant not found"})
        }

      price = variant['discount_price'] if variant['discount_available'] == True else variant['max_retail_price']
      product_details.append({
        'product_id': str(product['_id']),
        'product_name': product['name'],
        'variant_id': str(variant['_id']),
        'quantity': str(quantity),
        'price': price
      })

    logger.info("Initializing the collections...")
    orders = db.orders

    logger.info("Order processing...")
    total_price = order_data['total_price']

    order_status = 'Pending'
    order_date = datetime.datetime.now(datetime.timezone.utc)
    delivery_time = order_date + datetime.timedelta(minutes=15)


    order_document = {
      'user_email': user_email,
      'order_date': order_date,
      'order_items': product_details,
      'payment_mode': payment_mode,
      'delivery_charges': delivery_charges,
      'handling_charges': handling_charges,
      'delivery_address': delivery_address,
      'total_price': total_price,
      'total_quantity': total_quantity,
      'order_status': order_status,
      'delivery_time': delivery_time
    }

    result = orders.insert_one(order_document)
    logger.info(f"Order inserted with ID: {result.inserted_id}")

    return {
      'statusCode': 200,
      'body': json.dumps({
        'order_id': str(result.inserted_id),
        'order_date': order_date.isoformat(),
        'order_items': product_details,
        'payment_mode': payment_mode,
        'delivery_charges': delivery_charges,
        'handling_charges': handling_charges,
        'delivery_address': delivery_address,
        'total_price': total_price,
        'order_status': order_status,
        'delivery_time': delivery_time.isoformat(),
      }),
    }
  except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
    return {
      'statusCode': 500,
      'body': json.dumps({'errorMessage': str(e)})
    }
    
def get_order_handler(event, context, payload):
  try:
    logger.info(f"Received event: {json.dumps(event, indent=2)}")
    # print("Context Payload: ", context.payload)
    print("Event Payload: ", payload)

    # Extract order ID from the event path parameters
    if 'pathParameters' not in event or 'order_id' not in event['pathParameters']:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Order ID is missing"})
      }

    order_id = event['pathParameters']['order_id']
    if not ObjectId.is_valid(order_id):
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Invalid Order ID format"})
      }

    # Query the database for the order document
    orders = db.orders
    order_document = orders.find_one({"_id": ObjectId(order_id)})

    if not order_document:
      return {
        "statusCode": 404,
        "body": json.dumps({"errorMessage": "Order not found"})
      }

    order_document['_id'] = str(order_document['_id'])
    for item in order_document['order_items']:
      item['product_id'] = str(item['product_id'])
      item['variant_id'] = str(item['variant_id'])

    return {
      'statusCode': 200,
      'body': json.dumps(order_document, default=str)
    }

  except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
    return {
      'statusCode': 500,
      'body': json.dumps({'errorMessage': str(e)})
    }

def get_orders_handler(event, context, payload):  # sourcery skip: extract-method
  try:
    user_email = payload.get('email')
    if not user_email:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "User email is missing from the payload"})
      }
    
    logger.info(f"Fetching orders for user: {user_email}")
    
    orders = db.orders.find({"user_email": user_email})
    order_list = list(orders)

    return {
      "statusCode": 200,
      "body": json.dumps(order_list, default=str)
    }
  except Exception as e:
    error_message = str(e)
    logger.error(f"An error occurred: {error_message}")
    return {
      "statusCode": 500,
      "body": json.dumps({"errorMessage": error_message})
    }


import datetime
import json
import logging

from bson import ObjectId
from libs.utils import (
  json_unknown_type_handler, 
  validate_schema
)
from config.db import db
from config.schemas import order_schema

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def order_handler(event, context):
  try:
    logger.info(f"Received event: {json.dumps(event, indent=2)}")

    if 'body' not in event or not isinstance(event['body'], str):
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Request body is missing or empty"})
      }

    order_data = json.loads(event['body'])
    order_items = order_data.get('orderItems', [])
    if not order_items:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Order items are missing or empty"})
      }
    payment_mode = order_data.get('paymentMode', 'Paid Online')
    delivery_charges = order_data.get('deliveryCharges', 0)
    handling_charges = order_data.get('handlingCharges', 0)
    delivery_address = order_data.get('deliveryAddress', '')
    product_details = []
    total_price = 0
    for order_item in order_items:
      product_id = order_item.get('productId')
      variant_id = order_item.get('variantId')
      quantity = order_item.get('quantity')
      product = db.products.find_one({"_id": ObjectId(product_id)})
      if not product:
        logger.error(f"Product not found for order item: {order_item}")
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Product not found"})
        }
      logger.info("Product------------------------>", product)
      print(product)
      variant = db.variants.find_one({"_id": ObjectId(variant_id)})
      if not variant:
        logger.error(f"Variant not found for order item: {order_item}")
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Variant not found"})
        }
      logger.info("Variant------------------------>", variant)
      print(variant)
      
      if product and variant:
        product_details.append({
          'productId': product['_id'],
          'productName': product['name'],
          'variantId': variant['_id'],
          'quantity': quantity,
          'price': variant['max_retail_price']
        })
      else:
        logger.error(f"Product or variant not found for order item: {order_item}")
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Product or variant not found"})
        }

    logger.info("Initializing the collections...")
    orders = db.orders

    logger.info("Order processing...")
    total_price = order_data['totalPrice']

    order_status = 'Pending'
    order_date = datetime.datetime.now(datetime.timezone.utc)
    delivery_time = order_date + datetime.timedelta(minutes=15)  # Example: 15 minutes from now

    order_document = {
      'orderDate': order_date,
      'orderItems': product_details,
      'paymentMode': payment_mode,
      'deliveryCharges': delivery_charges,
      'handlingCharges': handling_charges,
      'deliveryAddress': delivery_address,
      'totalPrice': total_price,
      'orderStatus': order_status,
      'deliveryTime': delivery_time
    }
    
    result = orders.insert_one(order_document)
    logger.info(f"Order inserted with ID: {result.inserted_id}")

    return {
      'statusCode': 200,
      'body': json.dumps({
        'orderId': str(result.inserted_id),
        'orderDate': order_date.isoformat(),
        'orderItems': product_details,
        'paymentMode': payment_mode,
        'deliveryCharges': delivery_charges,
        'handlingCharges': handling_charges,
        'deliveryAddress': delivery_address,
        'totalPrice': total_price,
        'orderStatus': order_status,
        'deliveryTime': delivery_time.isoformat(),
      }),
    }
  except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
    return {
      'statusCode': 500,
      'body': json.dumps({'errorMessage': str(e)})
    }
    
def get_order_handler(event, context):
  try:
    logger.info(f"Received event: {json.dumps(event, indent=2)}")

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

    # Convert ObjectId fields to strings for JSON serialization
    order_document['_id'] = str(order_document['_id'])
    for item in order_document['orderItems']:
      item['productId'] = str(item['productId'])
      item['variantId'] = str(item['variantId'])

    return {
      'statusCode': 200,
      'body': json.dumps(order_document, default=str)  # Convert ObjectId to str
    }

  except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
    return {
      'statusCode': 500,
      'body': json.dumps({'errorMessage': str(e)})
    }
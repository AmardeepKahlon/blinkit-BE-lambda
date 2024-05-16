import datetime
import json
import logging

from bson import ObjectId

from config.db import db

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def order_handler(event, context):
  try:
    logger.info("Received event: " + json.dumps(event, indent=2))

    if 'body' in event and isinstance(event['body'], str):
      order_data = json.loads(event['body'])
      order_date = order_data['orderDate']
      order_items = order_data.get('orderItems', [])
      payment_mode = order_data.get('paymentMode', 'Paid Online')
      delivery_charges = order_data.get('deliveryCharges', 0)
      handling_charges = order_data.get('handlingCharges', 0)
      delivery_address = order_data.get('deliveryAddress', '')
    else:
      return {
        "statusCode": 400,
        "body": json.dumps({"errorMessage": "Request body is missing or empty"})
      }
    
    product_details = []
    total_price = 0
    for order_item in order_items:
      product_id = order_item.get('productId')
      variant_id = order_item.get('variantId')
      quantity = order_item.get('quantity')
      product = db.products.find_one({"_id": ObjectId(product_id)})
      variant = db.variants.find_one({"_id": ObjectId(variant_id)})
      if product and variant:
        product_details.append({
          'productId': product['_id'],
          'productName': product['name'],
          'variantId': variant['_id'],
          'variantName': variant['name'],
          'quantity': quantity,
          'price': variant['price']
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
    # Calculate total price
    total_price = sum(item['price'] * item['quantity'] for item in product_details)

    # Add order status and calculate delivery time
    order_status = 'Pending'  # You can set initial status as 'Pending'
    delivery_time = order_date + datetime.timedelta(minutes=15)  # Example: 15 minutes from now

    # Save the order details to the database
    # You can use your preferred database library or ORM to save data to the database

    # Construct response
    response = {
      'statusCode': 200,
      'body': json.dumps({
        'orderDate': order_date,
        'orderItems': product_details,
        'paymentMode': payment_mode,
        'deliveryCharges': delivery_charges,
        'handlingCharges': handling_charges,
        'deliveryAddress': delivery_address,
        'totalPrice': total_price,
        'orderStatus': order_status,
        'deliveryTime': delivery_time.isoformat()
      })
    }

    return response
  
  except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
    return {
      'statusCode': 500,
      'body': json.dumps({'errorMessage': str(e)})
    }
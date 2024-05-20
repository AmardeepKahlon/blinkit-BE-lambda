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
def order_handler(event, context):
  try:
    # logger.info("Received event:_________________>>>>>>>>>>>>>>>>>>>>>>>>>> " + json.dumps(event, indent=2))
    auth_header = event.get('headers', {}).get('Authorization')

    if not auth_header:
        return False, {"statusCode": 401, "body": json.dumps({"message": "Missing token"})}

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return False, {"statusCode": 401, "body": json.dumps({"message": "Invalid token format"})}    
    token = parts[1]
    print(token,'++++++++++++++++++++++++++++++++++++++++++>>>>>>>>>>>>>>')
    user_email=get_user_id_from_token(token,secret_key)
    

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
      if not product:
        logger.error(f"Product not found for order item: {order_item}")
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Product not found"})
        }
      # logger.info("Product------------------------>", product)
      # print(product)
      variant = db.variants.find_one({"_id": ObjectId(variant_id)})
      if not variant:
        logger.error(f"Variant not found for order item: {order_item}")
        return {
          "statusCode": 400,
          "body": json.dumps({"errorMessage": "Variant not found"})
        }
      # logger.info("Variant------------------------>", variant)
      # print(variant)
      
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
    # Calculate total price
    total_price = order_data['totalPrice']

    # Add order status and calculate delivery time
    order_status = 'Pending'
    
    
    # You can set initial status as 'Pending'
    order_date_date = datetime.datetime.strptime(order_date, "%Y-%m-%d %H:%M:%S")
    delivery_time = order_date_date + datetime.timedelta(minutes=15)  # Example: 15 minutes from now
    orderObj={
        'user_email': user_email,
        'orderDate': order_date,
        'orderItems': product_details,
        'paymentMode': payment_mode,
        'deliveryCharges': delivery_charges,
        'handlingCharges': handling_charges,
        'deliveryAddress': delivery_address,
        'totalPrice': total_price,
        'orderStatus': order_status,
        'deliveryTime': delivery_time.isoformat()
      }
    isValid,error_response=validate_schema(orderObj,order_schema)
    if not isValid:
      return error_response
    else:
       logger.info("Saving the order details to the database...")
       orders.insert_one(orderObj)

    # Save the order details to the database
    # You can use your preferred database library or ORM to save data to the database

    # Construct response
    response = {
      'statusCode': 200,
      'body': json.dumps({
        'orderDate': order_date,
        # 'orderItems': product_details,
        'paymentMode': payment_mode,
        'deliveryCharges': delivery_charges,
        'handlingCharges': handling_charges,
        'deliveryAddress': delivery_address,
        'totalPrice': total_price,
        'orderStatus': order_status,
        # 'deliveryTime': delivery_time.isoformat()
        "message":'order placed successfully'
        
      })
    }

    return response
  
  except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
    return {
      'statusCode': 500,
      'body': json.dumps({'errorMessage': str(e)})
    }

def get_allOrders_handler(event,context):
  # try:
     auth_header = event.get('headers', {}).get('Authorization')

     if not auth_header:
        return False, {"statusCode": 401, "body": json.dumps({"message": "Missing token"})}

     parts = auth_header.split()
     if len(parts) != 2 or parts[0].lower() != 'bearer':
        return False, {"statusCode": 401, "body": json.dumps({"message": "Invalid token format"})}    
     token = parts[1]
     print(token,'++++++++++++++++++++++++++++++++++++++++++>>>>>>>>>>>>>>')
     user_email=get_user_id_from_token(token,secret_key)
     print(user_email,'++++++++++++++++++++++++++++++++++++++++++++++++++====================')
    #  logger.info("Received event: " + json.dumps(event, indent=2))
     orders = db.orders.find({"user_email":user_email})
    #  print('orders----------------------------------->>>>>>',json.dumps(orders,indent=2) )
     order_list = list(orders)
     return {
      "statusCode": 200,
      "body": json.loads(json.dumps(order_list, default=json_unknown_type_handler))
      }
  # except Exception as e:
  #   error_message = str(e)
  #   return {
  #     "statusCode": 500,
  #     "body": json.dumps({"errorMessage": error_message})
  #   }

def get_user_id_from_token(token, secret):
    try:
        # Decode the token
        decoded_token = jwt.decode(token, secret, algorithms=["HS256"])
        print(decoded_token,'_------------------------------>>>>>>>>>>>>.')
        if decoded_token['role']=='USER':
          return decoded_token.get('email')
        else:
          return None
        
        # Extract user ID from the decoded token
    except jwt.ExpiredSignatureError:
        # Token has expired
        print("Token has expired")
        return None
    except jwt.JWTError:
        # Token is invalid
        print("Invalid token")
        return None

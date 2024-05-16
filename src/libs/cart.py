# import json
# import logging

# from bson import ObjectId

# from config.db import db
# from libs.utils import validate_schema
# from config.schemas import cart_schema

# logger = logging.getLogger()
# logger.setLevel(logging.INFO)

# def create_cart_handler(event, context):
#   try:
#     body = event.get("body", None)
#     if body is None:
#       return {
#         "statusCode": 400,
#         "body": json.dumps({"message": "Missing request body"})
#       }
    
#     is_valid, error_response = validate_schema(body, cart_schema)
#     if not is_valid:
#       return error_response
    
#     logger.info("Received event: " + json.dumps(event, indent=2))
      
#     logger.info("Initializing the collection")
#     carts = db.carts
    
#     cart_id = carts.insert_one(body).inserted_id
    
#     return {
#       "statusCode": 200,
#       "body": json.dumps({"message": "Cart created successfully", "cart_id": str(cart_id)})
#     }
#   except Exception as e:
#     error_message = str(e)
#     return {
#       "statusCode": 500,
#       "body": json.dumps({"errorMessage": error_message})
#     }

# def update_cart_handler(event, context):
#   try:
#     body = event.get("body", None)
#     if body is None:
#       return {
#         "statusCode": 400,
#         "body": json.dumps({"message": "Missing request body"})
#       }
    
#     is_valid, error_response = validate_schema(body, cart_schema)
#     if not is_valid:
#       return error_response
    
#     logger.info("Received event: " + json.dumps(event, indent=2))
    
#     cart_data = json.loads(body)
#     cart_id = cart_data.get("_id")
#     if isinstance(cart_id, str):
#       cart_data["_id"] = ObjectId(cart_id)
    
#     update_cart = db.carts.update_one({"_id": cart_data["_id"]}, {"$set": cart_data})
    
#     if update_cart.modified_count == 0:
#       return {
#         "statusCode": 404,
#         "body": json.dumps({"message": "Cart not found"})
#       }
#     else:
#       return {
#         "statusCode": 200,
#         "body": json.dumps({"message": "Cart updated successfully"})
#       }
#   except json.JSONDecodeError as e:
#     return {
#       "statusCode": 400,
#       "body": json.dumps({"message": "Invalid JSON format in request body"})
#     }
#   except Exception as e:
#     error_message = str(e)
#     return {
#       "statusCode": 500,
#       "body": json.dumps({"errorMessage": error_message})
#     }


# def delete_cart_handler(event, context):
#   try:
#     cart_id = event.get("pathParameters", {}).get("cart_id")
#     if not cart_id:
#       return {
#         "statusCode": 400,
#         "body": json.dumps({"message": "Cart ID is missing in request path"})
#       }
    
#     logger.info("Received event: " + json.dumps(event, indent=2))
    
#     delete_result = db.carts.delete_one({"_id": ObjectId(cart_id)})
    
#     if delete_result.deleted_count == 0:
#       return {
#         "statusCode": 404,
#         "body": json.dumps({"message": "Cart not found"})
#       }
#     else:
#       return {
#         "statusCode": 200,
#         "body": json.dumps({"message": "Cart deleted successfully"})
#       }
#   except Exception as e:
#     error_message = str(e)
#     return {
#       "statusCode": 500,
#       "body": json.dumps({"errorMessage": error_message})
#    }

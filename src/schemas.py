admin_schema = {
  "bsonType": "object",
  "required": ["fullname", "email", "password", "role"],
  "properties": {
    "fullname": {
      "bsonType": "string",
      "description": "Username of the admin"
    },
    "email": {
      "bsonType": "string",
      "description": "Email of the admin"
    },
    "password": {
      "bsonType": "string",
      "description": "Password of the admin"
    },
    "name": {
      "bsonType": "string",
      "description": "Name of the admin"
    },
    "role": {
      "bsonType": "string",
      "description": "Role of the admin"
    }
  }
}

user_schema = {
  "bsonType": "object",
  "required": ["fullname", "email", "password", "role"],
  "properties": {
    "fullname": {
      "bsonType": "string",
      "description": "full name of the user"
    },
    "password": {
      "bsonType": "string",
      "description": "Password of the user"
    },
    "contact": {
      "bsonType": "string",
      "description": "Contact of the user"
    },
    "email": {
      "bsonType": "string",
      "description": "Email of the user"
    },
    "address": {
      "bsonType": "string",
      "description": "Address of the user"
    },
    "role": {
      "bsonType": "string",
      "description": "Role of the user"
    },
    "team": {
      "bsonType": "string",
      "description": "Team of the user"
    },
    "shift": {
      "bsonType": "string",
      "description": "Shift of the user"
    }
  }
}

category_schema = {
  "bsonType": "object",
  "required": ["name", "image_url"],
  "properties": {
    "name": {
      "bsonType": "string",
      "description": "Name of the category"
    },
    "image_url": {
      "bsonType": "string",
      "description": "URL of the category image"
    }
  }
}

update_category_schema = {
  "bsonType": "object",
  "required": ["name", "image_url", "_id"],
  "properties": {
    "name": {
      "bsonType": "string",
      "description": "Name of the category"
    },
    "image_url": {
      "bsonType": "string",
      "description": "URL of the category image"
    },
    "_id": {
      "bsonType": "string",
      "description": "ID of the category"
    }
  }
}

subcategory_schema = {
  "bsonType": "object",
  "required": ["name", "image_url", "category_id"],
  "properties": {
    "name": {
      "bsonType": "string",
      "description": "Name of the subcategory"
    },
    "image_url": {
      "bsonType": "string",
      "description": "URL of the category image"
    },
    "category_id": {
      "bsonType": "string",
      "description": "ID of the parent category"
    }
  }
}

update_subcategory_schema = {
  "bsonType": "object",
  "required": ["name", "image_url", "category_id", "_id"],
  "properties": {
    "name": {
      "bsonType": "string",
      "description": "Name of the subcategory"
    },
    "image_url": {
      "bsonType": "string",
      "description": "URL of the category image"
    },
    "category_id": {
      "bsonType": "string",
      "description": "ID of the parent category"
    },
    "_id": {
      "bsonType": "string",
      "description": "ID of the subcategory"
    }
  }
}

product_schema = {
  "bsonType": "object",
  "required": ["name", "image_url", "company_name", "product_description", "number_of_variants", "subcategory_id"],
  "properties": {
    "name": {
      "bsonType": "string",
      "description": "Name of the product"
    },
    "image_url": {
      "bsonType": "string",
      "description": "URL of the category image"
    },
    "company_name": {
      "bsonType": "string",
      "description": "Name of the company of the product"
    },
    "product_description": {
      "bsonType": "string",
      "description": "Description of the product"
    },
    "number_of_variants": {
      "bsonType": "string",
      "description": "Number of variants of the product"
    },
    "subcategory_id": {
      "bsonType": "string",
      "description": "ID of the parent subcategory"
    }
  }
}

update_product_schema = {
  "bsonType": "object",
  "required": ["_id"],
  "properties": {
    "name": {
      "bsonType": "string",
      "description": "Name of the product"
    },
    "image_url": {
      "bsonType": "string",
      "description": "URL of the category image"
    },
    "company_name": {
      "bsonType": "string",
      "description": "Name of the company of the product"
    },
    "product_description": {
      "bsonType": "string",
      "description": "Description of the product"
    },
    "number_of_variants": {
      "bsonType": "string",
      "description": "Number of variants of the product"
    },
    "subcategory_id": {
      "bsonType": "string",
      "description": "ID of the parent subcategory"
    },
    "_id": {
      "bsonType": "string",
      "description": "ID of the product"
    }
  }
}

product_variant_schema = {
  "bsonType": "object",
  "required": ["image_urls", "discount_available", "max_retail_price", "units", "total_quantity"],
  "properties": {
    "image_urls": {
      "bsonType": "array",
      "description": "Image URLs of the product"
    },
    "discount_available": {
      "bsonType": "bool",
      "description": "Discount availability for the product"
    },
    "max_retail_price": {
      "bsonType": "string",
      "description": "Price of the product"
    },
    "units": {
      "bsonType": "string",
      "description": "Units of the product"
    },
    "total_quantity": {
      "bsonType": "string",
      "description": "Total quantity of the product"
    },
    "discount_price": {
      "bsonType": "string",
      "description": "Discount price of the product"
    },
    "discount_percentage": {
      "bsonType": "string",
      "description": "Discount percentage of the product"
    }
  }
}

update_product_variant_schema = {
  "bsonType": "object",
  "required": ["_id"],
  "properties": {
    "image_urls": {
      "bsonType": "array",
      "description": "Image URLs of the product"
    },
    "discount_available": {
      "bsonType": "bool",
      "description": "Discount availability for the product"
    },
    "max_retail_price": {
      "bsonType": "string",
      "description": "Price of the product"
    },
    "units": {
      "bsonType": "string",
      "description": "Units of the product"
    },
    "total_quantity": {
      "bsonType": "string",
      "description": "Total quantity of the product"
    },
    "discount_price": {
      "bsonType": "string",
      "description": "Discount price of the product"
    },
    "discount_percentage": {
      "bsonType": "string",
      "description": "Discount percentage of the product"
    },
    "_id": {
      "bsonType": "string",
      "description": "ID of the product"
    }
  }
}
# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "e64c53cb-f4b5-421e-8f0d-cd30722044b6",
# META       "default_lakehouse_name": "lh_orders_silver",
# META       "default_lakehouse_workspace_id": "e7bb9e44-d714-4f11-b4c1-9a3984caa0f3",
# META       "known_lakehouses": [
# META         {
# META           "id": "e64c53cb-f4b5-421e-8f0d-cd30722044b6"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

from pyspark.sql.functions import col, to_timestamp, trim, lower

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Rohe Dateien aus dem Bronze-Shortcut lesen
df_orders_raw = spark.read.option("header", "true").csv("Files/bronze/olist_orders_dataset.csv")

df_orders_raw.printSchema()
display(df_orders_raw.limit(5))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_orders_silver = (
    df_orders_raw
    # Zeitstempel-Spalten von String -> echten Timestamp
    .withColumn("order_purchase_timestamp", to_timestamp("order_purchase_timestamp"))
    .withColumn("order_approved_at", to_timestamp("order_approved_at"))
    .withColumn("order_delivered_carrier_date", to_timestamp("order_delivered_carrier_date"))
    .withColumn("order_delivered_customer_date", to_timestamp("order_delivered_customer_date"))
    .withColumn("order_estimated_delivery_date", to_timestamp("order_estimated_delivery_date"))
    # Duplikate auf Basis des Primärschlüssels entfernen
    .dropDuplicates(["order_id"])
)

# Als Delta-Tabelle in den Tables-Bereich des Lakehouse schreiben
df_orders_silver.write.mode("overwrite").format("delta").saveAsTable("orders_silver")

print("Zeilen:", df_orders_silver.count())
display(df_orders_silver.limit(5))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Rohe Dateien aus dem Bronze-Shortcut lesen
df_items_raw = spark.read.option("header", "true").csv("Files/bronze/olist_order_items_dataset.csv")

df_order_items_raw.printSchema()
display(df_items_raw.limit(5))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_items_silver = (
    df_items_raw
    .withColumn("price", col("price").cast("decimal(10,2)"))
    .withColumn("freight_value", col("freight_value").cast("decimal(10,2)"))
    .withColumn("order_item_id", col("order_item_id").cast("int"))
    .withColumn("shipping_limit_date", to_timestamp("shipping_limit_date"))
)

df_items_silver.write.mode("overwrite").format("delta").saveAsTable("order_items_silver")

print("Zeilen:", df_items_silver.count())
display(df_items_silver.limit(5))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Rohe Dateien aus dem Bronze-Shortcut lesen
df_customers_raw = spark.read.option("header", "true").csv("Files/bronze/olist_customers_dataset.csv")

df_customers_raw.printSchema()
display(df_customers_raw.limit(5))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_customers_silver = (
    df_customers_raw
    .withColumn("customer_zip_code_prefix", col("customer_zip_code_prefix").cast("int"))
    .dropDuplicates(["customer_id"])
)

df_customers_silver.write.mode("overwrite").format("delta").saveAsTable("customers_silver")

print("customers:", df_customers_silver.count())
display(df_customers_silver.limit(5))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Rohe Dateien aus dem Bronze-Shortcut lesen
df_products_raw = spark.read.option("header", "true").csv("Files/bronze/olist_products_dataset.csv")
df_category_translation = spark.read.option("header", "true").csv("Files/bronze/product_category_name_translation.csv")

df_products_raw.printSchema()
display(df_products_raw.limit(5))

df_category_translation.printSchema()
display(df_category_translation.limit(5))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_products_silver = (
    df_products_raw
    # portugiesischen Kategorienamen ins Englische übersetzen
    .join(df_category_translation, on="product_category_name", how="left")
    # numerische Attribute typisieren
    .withColumn("product_weight_g", col("product_weight_g").cast("int"))
    .withColumn("product_length_cm", col("product_length_cm").cast("int"))
    .withColumn("product_height_cm", col("product_height_cm").cast("int"))
    .withColumn("product_width_cm", col("product_width_cm").cast("int"))
    # nur die relevanten Spalten behalten
    .select(
        "product_id",
        col("product_category_name_english").alias("category"),
        "product_weight_g",
        "product_length_cm",
        "product_height_cm",
        "product_width_cm"
    )
    .dropDuplicates(["product_id"])
)

df_products_silver.write.mode("overwrite").format("delta").saveAsTable("products_silver")

print("products:", df_products_silver.count())
display(df_products_silver.limit(5))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Rohe Dateien aus dem Bronze-Shortcut lesen
df_sellers_raw = spark.read.option("header", "true").csv("Files/bronze/olist_sellers_dataset.csv")

df_sellers_raw.printSchema()
display(df_sellers_raw.limit(5))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_sellers_silver = (
    df_sellers_raw
    .withColumn("seller_zip_code_prefix", col("seller_zip_code_prefix").cast("int"))
    .withColumn("seller_city", trim(lower(col("seller_city"))))
    .dropDuplicates(["seller_id"])
)

df_sellers_silver.write.mode("overwrite").format("delta").saveAsTable("sellers_silver")

print("sellers:", df_sellers_silver.count())
display(df_sellers_silver.limit(5))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

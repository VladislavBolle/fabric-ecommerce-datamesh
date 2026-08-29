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

# Rohe Dateien aus dem Bronze-Shortcut lesen
df_orders_raw = spark.read.option("header", "true").csv("Files/bronze/olist_orders_dataset.csv")
df_items_raw = spark.read.option("header", "true").csv("Files/bronze/olist_order_items_dataset.csv")

df_orders_raw.printSchema()
display(df_orders_raw.limit(5))

df_order_items_raw.printSchema()
display(df_items_raw.limit(5))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import col, to_timestamp

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

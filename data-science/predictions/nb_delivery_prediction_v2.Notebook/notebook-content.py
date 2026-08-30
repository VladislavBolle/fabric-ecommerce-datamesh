# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "3e7d7f11-3372-4c46-9459-0cdaeca8165b",
# META       "default_lakehouse_name": "lh_datascience",
# META       "default_lakehouse_workspace_id": "d8fe88f6-5b50-4c42-9893-5835fdf47487",
# META       "known_lakehouses": [
# META         {
# META           "id": "3e7d7f11-3372-4c46-9459-0cdaeca8165b"
# META         }
# META       ]
# META     }
# META   }
# META }

# CELL ********************

df_orders    = spark.read.table("orders_silver")
df_items     = spark.read.table("order_items_silver")
df_customers = spark.read.table("customers_silver")
df_products  = spark.read.table("products_silver")
df_sellers   = spark.read.table("sellers_silver")

print("sellers:", df_sellers.count(), "Zeilen")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import col, datediff, month

df_orders_clean = (
    df_orders
    .filter(col("order_status") == "delivered")
    .filter(col("order_delivered_customer_date").isNotNull())
    .filter(col("order_purchase_timestamp").isNotNull())
    .withColumn("delivery_days",
                datediff("order_delivered_customer_date", "order_purchase_timestamp"))
    .withColumn("order_month", month("order_purchase_timestamp"))
    .filter((col("delivery_days") >= 0) & (col("delivery_days") <= 60))
    .select("order_id", "customer_id", "delivery_days", "order_month")
)
print("Bestellungen nach Bereinigung:", df_orders_clean.count())

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import sum as _sum, avg, count, first
from pyspark.sql.window import Window
import pyspark.sql.functions as F

# Positionen aggregieren (wie vorher)
df_items_agg = (
    df_items.groupBy("order_id")
    .agg(_sum("price").alias("total_price"),
         _sum("freight_value").alias("total_freight"),
         count("*").alias("n_items"))
)

# Produkt-Merkmale (wie vorher)
df_items_products = (
    df_items.join(df_products, on="product_id", how="left")
    .groupBy("order_id")
    .agg(avg("product_weight_g").alias("avg_weight_g"),
         avg(col("product_length_cm")*col("product_height_cm")*col("product_width_cm")).alias("avg_volume_cm3"))
)

# NEU: Verkäufer-Bundesstaat je Bestellung (häufigster Verkäufer-State)
df_seller_state = (
    df_items.join(df_sellers, on="seller_id", how="left")
    .groupBy("order_id", "seller_state")
    .agg(count("*").alias("cnt"))
)
w = Window.partitionBy("order_id").orderBy(F.desc("cnt"))
df_seller_state = (
    df_seller_state
    .withColumn("rn", F.row_number().over(w))
    .filter(col("rn") == 1)
    .select("order_id", col("seller_state").alias("seller_state"))
)

# Kunden-State
df_cust = df_customers.select("customer_id", "customer_state")

# alles zusammenführen
df_features = (
    df_orders_clean
    .join(df_items_agg,      on="order_id",     how="left")
    .join(df_items_products, on="order_id",     how="left")
    .join(df_seller_state,   on="order_id",     how="left")
    .join(df_cust,           on="customer_id",  how="left")
)

print("Feature-Tabelle:", df_features.count(), "Zeilen")
df_features.show(5)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import pandas as pd

pdf = df_features.drop("order_id", "customer_id").toPandas()

# fehlende numerische Werte mit Median auffüllen
for c in ["avg_weight_g", "avg_volume_cm3", "total_price", "total_freight", "n_items"]:
    pdf[c] = pdf[c].fillna(pdf[c].median())

# fehlende Kategorien (falls ein seller_state NULL blieb) auffüllen
pdf["seller_state"]   = pdf["seller_state"].fillna("unknown")
pdf["customer_state"] = pdf["customer_state"].fillna("unknown")

# kategoriale Spalten markieren
for c in ["order_month", "seller_state", "customer_state"]:
    pdf[c] = pdf[c].astype("category")

print("Fehlende Werte:", pdf.isnull().sum().sum())
print("Spalten:", list(pdf.columns))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from sklearn.model_selection import train_test_split

y = pdf["delivery_days"]
X = pd.get_dummies(pdf.drop(columns=["delivery_days"]),
                   columns=["order_month", "seller_state", "customer_state"],
                   drop_first=True)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print("Features nach Encoding:", X.shape[1])

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import mlflow
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

mlflow.set_experiment("delivery_prediction")

with mlflow.start_run(run_name="v2_with_seller_state"):
    params = dict(n_estimators=100, max_depth=15, min_samples_leaf=20,
                  n_jobs=-1, random_state=42)

    model = RandomForestRegressor(**params)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mae  = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    # Parameter und Metriken loggen
    mlflow.log_params(params)
    mlflow.log_param("n_features", X.shape[1])
    mlflow.log_metric("MAE", mae)
    mlflow.log_metric("RMSE", rmse)
    mlflow.sklearn.log_model(model, "model")

    print(f"MAE:  {mae:.2f} Tage")
    print(f"RMSE: {rmse:.2f} Tage")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import round as _round, col, abs as _abs

df_predictions.write \
    .mode("overwrite") \
    .option("overwriteSchema", "true") \
    .format("delta") \
    .saveAsTable("delivery_predictions")

# Vorhersagen mit echten Werten zusammenführen
results_pdf = X_test.copy()
results_pdf["delivery_days_actual"]    = y_test.values
results_pdf["delivery_days_predicted"] = y_pred

df_predictions = (
    spark.createDataFrame(
        results_pdf[["delivery_days_actual", "delivery_days_predicted"]]
    )
    .withColumn("delivery_days_predicted", _round("delivery_days_predicted", 1))
    .withColumn("abs_error", _abs(col("delivery_days_actual") - col("delivery_days_predicted")))
)

df_predictions.write.mode("overwrite").format("delta").saveAsTable("delivery_predictions")

print("Datenprodukt 'delivery_predictions':", df_predictions.count(), "Zeilen")
display(df_predictions.limit(5))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

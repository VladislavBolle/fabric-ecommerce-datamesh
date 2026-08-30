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

from pyspark.sql.functions import col, datediff, month, sum as _sum, avg, count

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_orders    = spark.read.table("orders_silver")
df_items     = spark.read.table("order_items_silver")
df_customers = spark.read.table("customers_silver")
df_products  = spark.read.table("products_silver")

for name, df in [("orders", df_orders), ("items", df_items),
                 ("customers", df_customers), ("products", df_products)]:
    print(f"{name}: {df.count()} Zeilen")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

df_orders_clean = (
    df_orders
    # nur tatsächlich gelieferte Bestellungen mit vorhandenem Lieferdatum
    .filter(col("order_status") == "delivered")
    .filter(col("order_delivered_customer_date").isNotNull())
    .filter(col("order_purchase_timestamp").isNotNull())
    # Zielgröße: Liefertage
    .withColumn("delivery_days",
                datediff("order_delivered_customer_date", "order_purchase_timestamp"))
    # Bestellmonat als (später kategoriales) Merkmal
    .withColumn("order_month", month("order_purchase_timestamp"))
    # unplausible Werte entfernen (negative oder extreme Ausreißer)
    .filter((col("delivery_days") >= 0) & (col("delivery_days") <= 60))
    .select("order_id", "customer_id", "delivery_days", "order_month")
)

print("Bestellungen nach Bereinigung:", df_orders_clean.count())
df_orders_clean.select("delivery_days").summary("min", "25%", "50%", "75%", "max", "mean").show()

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

# Positionen je Bestellung aggregieren (eine Bestellung hat mehrere Artikel)
df_items_agg = (
    df_items
    .groupBy("order_id")
    .agg(
        _sum("price").alias("total_price"),
        _sum("freight_value").alias("total_freight"),
        count("*").alias("n_items"),
        avg("product_id").alias("_dummy")   # Platzhalter, gleich ersetzt
    )
    .drop("_dummy")
)

# Produkt-Merkmale: pro Bestellung das durchschnittliche Gewicht/Volumen der Artikel
df_items_products = (
    df_items
    .join(df_products, on="product_id", how="left")
    .groupBy("order_id")
    .agg(
        avg("product_weight_g").alias("avg_weight_g"),
        avg(col("product_length_cm") * col("product_height_cm") * col("product_width_cm")).alias("avg_volume_cm3")
    )
)

# Kunden-Bundesstaat
df_cust = df_customers.select("customer_id", "customer_state")

# alles zusammenführen
df_features = (
    df_orders_clean
    .join(df_items_agg, on="order_id", how="left")
    .join(df_items_products, on="order_id", how="left")
    .join(df_cust, on="customer_id", how="left")
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

# nur die Modell-Spalten nach Pandas holen (order_id/customer_id brauchen wir nicht mehr)
pdf = (
    df_features
    .drop("order_id", "customer_id")
    .toPandas()
)

# fehlende Produktdaten mit dem Median auffüllen
for c in ["avg_weight_g", "avg_volume_cm3", "total_price", "total_freight", "n_items"]:
    pdf[c] = pdf[c].fillna(pdf[c].median())

# order_month und customer_state sind kategorial -> als category markieren
pdf["order_month"]    = pdf["order_month"].astype("category")
pdf["customer_state"] = pdf["customer_state"].astype("category")

print("Zeilen:", len(pdf), "| Spalten:", list(pdf.columns))
print("Fehlende Werte pro Spalte:")
print(pdf.isnull().sum())

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from sklearn.model_selection import train_test_split

# Ziel (y) und Merkmale (X) trennen
y = pdf["delivery_days"]
X = pdf.drop(columns=["delivery_days"])

# kategoriale Spalten in 0/1-Spalten umwandeln (One-Hot-Encoding)
X = pd.get_dummies(X, columns=["order_month", "customer_state"], drop_first=True)

# 80 % Training, 20 % Test
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("Trainingsdaten:", X_train.shape)
print("Testdaten:     ", X_test.shape)
print("Anzahl Features nach Encoding:", X.shape[1])

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from sklearn.ensemble import RandomForestRegressor

model = RandomForestRegressor(
    n_estimators=100,      # 100 Entscheidungsbäume
    max_depth=15,          # Tiefe begrenzen (verhindert Overfitting)
    min_samples_leaf=20,   # jedes Blatt braucht min. 20 Beobachtungen
    n_jobs=-1,             # alle CPU-Kerne nutzen
    random_state=42
)

model.fit(X_train, y_train)
print("Modell trainiert.")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

# Vorhersage auf den Testdaten
y_pred = model.predict(X_test)

mae  = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))

print(f"MAE  (mittlerer absoluter Fehler): {mae:.2f} Tage")
print(f"RMSE (Wurzel des mittleren Fehlerquadrats): {rmse:.2f} Tage")

# Feature-Importances: welche Merkmale treiben die Lieferzeit?
importances = (
    pd.Series(model.feature_importances_, index=X.columns)
    .sort_values(ascending=False)
    .head(10)
)
print("\nTop 10 wichtigste Merkmale:")
print(importances)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql.functions import round as _round

# Vorhersagen mit den echten Werten zusammenführen
results_pdf = X_test.copy()
results_pdf["delivery_days_actual"]    = y_test.values
results_pdf["delivery_days_predicted"] = y_pred

# als Spark-DataFrame zurück und als Delta-Tabelle speichern
df_predictions = spark.createDataFrame(
    results_pdf[["delivery_days_actual", "delivery_days_predicted"]]
).withColumn("delivery_days_predicted", _round("delivery_days_predicted", 1))

df_predictions.write.mode("overwrite").format("delta").saveAsTable("delivery_predictions")

print("Datenprodukt 'delivery_predictions' gespeichert:", df_predictions.count(), "Zeilen")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

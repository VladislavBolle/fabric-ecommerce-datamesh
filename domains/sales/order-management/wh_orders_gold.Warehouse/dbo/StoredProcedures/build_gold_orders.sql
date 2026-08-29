CREATE   PROCEDURE dbo.build_gold_orders AS
BEGIN
    -- Datumsdimension
    DROP TABLE IF EXISTS dbo.dim_date;
    CREATE TABLE dbo.dim_date AS
    SELECT DISTINCT
        CAST(order_purchase_timestamp AS DATE)                          AS date_key,
        YEAR(order_purchase_timestamp)                                  AS year,
        MONTH(order_purchase_timestamp)                                 AS month,
        DAY(order_purchase_timestamp)                                   AS day,
        CAST(DATENAME(WEEKDAY, order_purchase_timestamp) AS VARCHAR(20)) AS weekday_name,
        DATEPART(QUARTER, order_purchase_timestamp)                     AS quarter
    FROM lh_orders_silver.dbo.orders_silver
    WHERE order_purchase_timestamp IS NOT NULL;

    -- Bestell-Dimension
    DROP TABLE IF EXISTS dbo.dim_order;
    CREATE TABLE dbo.dim_order AS
    SELECT
        order_id, customer_id, order_status,
        CAST(order_purchase_timestamp AS DATE)  AS order_date,
        order_delivered_customer_date,
        order_estimated_delivery_date,
        DATEDIFF(DAY, order_purchase_timestamp, order_delivered_customer_date) AS delivery_days
    FROM lh_orders_silver.dbo.orders_silver;

    -- Kunden-Dimension
    DROP TABLE IF EXISTS dbo.dim_customer;
    CREATE TABLE dbo.dim_customer AS
    SELECT
        customer_id,
        customer_unique_id,
        customer_zip_code_prefix,
        customer_city,
        customer_state
    FROM lh_orders_silver.dbo.customers_silver;

    -- Produkt-Dimension
    DROP TABLE IF EXISTS dbo.dim_product;
    CREATE TABLE dbo.dim_product AS
    SELECT
        product_id,
        category,
        product_weight_g,
        product_length_cm,
        product_height_cm,
        product_width_cm
    FROM lh_orders_silver.dbo.products_silver;

    -- Faktentabelle (Positionsebene, jetzt mit customer_id)
    DROP TABLE IF EXISTS dbo.fact_order_items;
    CREATE TABLE dbo.fact_order_items AS
    SELECT
        oi.order_id,
        oi.order_item_id,
        oi.product_id,
        oi.seller_id,
        o.customer_id,
        CAST(o.order_purchase_timestamp AS DATE)  AS order_date,
        oi.price,
        oi.freight_value,
        (oi.price + oi.freight_value)             AS total_item_value
    FROM lh_orders_silver.dbo.order_items_silver AS oi
    LEFT JOIN lh_orders_silver.dbo.orders_silver AS o
        ON oi.order_id = o.order_id;
END;
CREATE TABLE [dbo].[dim_order] (

	[order_id] varchar(8000) NULL, 
	[customer_id] varchar(8000) NULL, 
	[order_status] varchar(8000) NULL, 
	[order_date] date NULL, 
	[order_delivered_customer_date] datetime2(6) NULL, 
	[order_estimated_delivery_date] datetime2(6) NULL, 
	[delivery_days] int NULL
);
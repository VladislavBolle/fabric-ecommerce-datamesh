CREATE TABLE [dbo].[fact_order_items] (

	[order_id] varchar(8000) NULL, 
	[order_item_id] int NULL, 
	[product_id] varchar(8000) NULL, 
	[seller_id] varchar(8000) NULL, 
	[customer_id] varchar(8000) NULL, 
	[order_date] date NULL, 
	[price] decimal(10,2) NULL, 
	[freight_value] decimal(10,2) NULL, 
	[total_item_value] decimal(11,2) NULL
);
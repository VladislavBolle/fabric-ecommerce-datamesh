CREATE TABLE [dbo].[dim_customer] (

	[customer_id] varchar(8000) NULL, 
	[customer_unique_id] varchar(8000) NULL, 
	[customer_zip_code_prefix] int NULL, 
	[customer_city] varchar(8000) NULL, 
	[customer_state] varchar(8000) NULL
);
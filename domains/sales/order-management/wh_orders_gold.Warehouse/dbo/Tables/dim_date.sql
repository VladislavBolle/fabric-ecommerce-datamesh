CREATE TABLE [dbo].[dim_date] (

	[date_key] date NULL, 
	[year] int NULL, 
	[month] int NULL, 
	[day] int NULL, 
	[weekday_name] varchar(20) NULL, 
	[quarter] int NULL
);
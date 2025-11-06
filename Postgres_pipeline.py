import requests
import json
import pandas as pd
import csv
import psycopg2

# Read into a DataFrame
propertyRecords_df = pd.read_json('PropertyRecords.json')

# Transformation Layer
# 1st Convert dictionary column to string
propertyRecords_df['features'] = propertyRecords_df['features'].apply(json.dumps)

# 2nd Fill missing values with defaults or placeholders
propertyRecords_df.fillna({
    'assessorID': 'Unknown',
    'legalDescription': 'Not available',
    'ownerOccupied': 0,
    'squareFootage': 0,
    'subdivision': 'Not available',
    'yearBuilt': 0,
    'zoning' : 'Unknown',
    'lotSize': 0,
    'propertyType': 'Unknown',
    'lastSalePrice': 0,
    'lastSaleDate': 'Not available',
    'bathrooms': 0,
    'taxAssessment': 'Not available',
    'propertyTaxes': 'Not available',
    'owner': 'Unknown',
    'bedrooms': 0,
    'addressLine2': 'Not available',

   }, inplace=True)

# Create the fact table
fact_columns = ['addressLine1', 'city', 'state', 'zipCode', 'formattedAddress', 'squareFootage', 'yearBuilt',
               'bedrooms','bathrooms', 'lotSize', 'propertyType', 'longitude', 'latitude']
fact_table = propertyRecords_df[fact_columns]

# Create Location Dimension
location_dim = propertyRecords_df[['addressLine1', 'city', 'state', 'zipCode', 'county', 'longitude', 'latitude']].drop_duplicates().reset_index(drop=True)
location_dim.index.name = 'location_id'

# Create Sales Dimension
sales_dim = propertyRecords_df[['lastSalePrice', 'lastSaleDate']].drop_duplicates().reset_index(drop=True)
sales_dim.index.name = 'sales_id'

# Create Property Features Dimension
features_dim = propertyRecords_df[['features', 'propertyType', 'zoning']].drop_duplicates().reset_index(drop=True)
features_dim.index.name = 'features_id'

fact_table.to_csv('property_fact.csv', index=False)
location_dim.to_csv('location_dimension.csv', index=True)
sales_dim.to_csv('sales_dimension.csv', index=True)
features_dim.to_csv('features_dimension.csv', index=True)

# Loading Layer
# Develop a function to connect to pgadmin
def get_db_connection():
  connection = psycopg2.connect(
      host="localhost",
      port=5432,
      dbname="postgres",
      user="postgres",
      password="admin456"
  )
  return connection

  conn = get_db_connection()

# Create tables
def create_tables():
  conn = get_db_connection()
  cursor = conn.cursor()
  create_table_query = '''-- Drop existing tables
                          DROP TABLE IF EXISTS Zapbank.fact_table;
                          DROP TABLE IF EXISTS Zapbank.location_dim;
                          DROP TABLE IF EXISTS Zapbank.sales_dim;
                          DROP TABLE IF EXISTS Zapbank.features_dim;

                           -- Create the schema if it doesn't exist
                          CREATE SCHEMA IF NOT EXISTS Zapbank;
                         
                          -- Create new tables
                          CREATE TABLE Zapbank.fact_table (
                            addressLine1 VARCHAR(255),
                            city VARCHAR(100),
                            state VARCHAR(50),
                            zipCode INTEGER,
                            formattedAddress VARCHAR(255),
                            squareFootage FLOAT,
                            yearBuilt FLOAT,
                            bedrooms FLOAT,
                            bathrooms FLOAT,
                            lotSize FLOAT,
                            propertyType VARCHAR(100),
                            longitude FLOAT,
                            latitude FLOAT
                          );

                          CREATE TABLE Zapbank.location_dim (
                            location_id SERIAL PRIMARY KEY,
                            addressLine1 VARCHAR(255),
                            city VARCHAR (100),
                            state VARCHAR(50),
                            zipCode INTEGER,
                            county VARCHAR(100),
                            longitude FLOAT,
                            latitude FLOAT
                          );

                          CREATE TABLE Zapbank.sales_dim (
                            sales_id SERIAL PRIMARY KEY,
                            lastSalePrice FLOAT,
                            lastSaleDate DATE
                          );

                          CREATE TABLE Zapbank.features_dim(
                            features_id SERIAL PRIMARY KEY,
                            features TEXT,
                            propertyType VARCHAR(100),
                            zoning VARCHAR(100)
                          );'''
  
  cursor.execute(create_table_query)
  conn.commit()
  cursor.close()
  conn.close()

create_tables()

# Create a function to load the csv data into the database
def load_data_from_csv_to_table(csv_path, table_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            placeholders = ', '.join(['%s'] * len(row))
            query = f'INSERT INTO {table_name} VALUES ({placeholders});'
            cursor.execute(query, row)

    conn.commit()
    cursor.close()
    conn.close()

# Create a function to load the csv data into the database
def load_data_from_csv_to_table(csv_path, table_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        for row in reader:
            placeholders = ', '.join(['%s'] * len(row))
            query = f'INSERT INTO {table_name} VALUES ({placeholders});'
            cursor.execute(query, row)
    conn.commit()
    cursor.close()
    conn.close()

# fact table
fact_csv_path = (r'C:\Users\USER\Desktop\Projects\PERSONAL PROJECTS\FREE PROJECTS\Real Estate Data Evolution\property_fact.csv')
load_data_from_csv_to_table(fact_csv_path, 'Zapbank.fact_table')

# location dimension table
location_csv_path = (r'C:\Users\USER\Desktop\Projects\PERSONAL PROJECTS\FREE PROJECTS\Real Estate Data Evolution\location_dimension.csv')
load_data_from_csv_to_table(location_csv_path, 'Zapbank.location_dim')

# features table
features_csv_path = (r'C:\Users\USER\Desktop\Projects\PERSONAL PROJECTS\FREE PROJECTS\Real Estate Data Evolution\features_dimension.csv')
load_data_from_csv_to_table(features_csv_path, 'Zapbank.features_dim')

def load_data_from_csv_to_sales_table(csv_path, table_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    with open(csv_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        next(reader)  # Skip the header row
        
        for row in reader:
            # Convert empty strings (or 'Not available') in date column to None (NULL in SQL)
            row = [None if (cell == '' or cell == 'Not available') and col_name == 'lastSaleDate' else cell for cell, col_name in zip(row, sales_dim_columns)]

            placeholders = ', '.join(['%s'] * len(row))
            query = f'INSERT INTO {table_name} VALUES ({placeholders});'
            cursor.execute(query, row)

    conn.commit()
    cursor.close()
    conn.close()

# define the columns names in sales_dim table
sales_dim_columns = ['sales_id', 'lastSalePrice', 'lastSaleDate']

# features table
sales_csv_path = (r'C:\Users\USER\Desktop\Projects\PERSONAL PROJECTS\FREE PROJECTS\Real Estate Data Evolution\sales_dimension.csv')
load_data_from_csv_to_sales_table(sales_csv_path, 'Zapbank.sales_dim')

print('All Data has been loaded successfully into their respective schema and tables')          
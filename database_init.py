import pandas as pd
import sqlite3

###
# This python file is used to initiate sqlite database, and store our data in it
# DISCLAIMER: At first I imported raw data to the sql and then did the preprocessing,
# but I believe it is not efficient to preprocess data every time when retrieving it from databse.
# Therefore to decrease redundancy, I preprocessed the data before importing it.
###

# store data in pandas dataframe to preprocess it before storing to database
hourly_data = pd.read_csv(
    'Actual Generation per Production Type_202001010000-202101010000.csv')

# dropping Area column as for our task we only work for DK2 (Eastern Denmark) zone
hourly_data.drop(['Area'], axis=1, inplace=True)

# dropping all columns with 1 unique value of ("n/e") in it, as those features would not help in our analysis
for col in hourly_data.columns:
    if hourly_data[col].nunique() == 1:
        hourly_data.drop(col, inplace=True, axis=1)


# Also it is good to have date data in datetime format, and to change "." notation to "-", as not all databases/matrix manipulation libraries
# understand "." notation
hourly_data['MTU'] = hourly_data['MTU'].str[:16]
hourly_data['MTU'] = hourly_data['MTU'].str.replace(".", "-")

# Ultimately, combining wind offshore and onshore columns, as we have 1 intentisty for both of them
hourly_data['wind_total'] = hourly_data[list(
    ['Wind Offshore  - Actual Aggregated [MW]', 'Wind Onshore  - Actual Aggregated [MW]'])].sum(axis=1)
hourly_data.drop(['Wind Offshore  - Actual Aggregated [MW]',
                  'Wind Onshore  - Actual Aggregated [MW]'], axis=1, inplace=True)

# With preanalysis of task and trying to understand carbon intensity, I came to conclusion that we would need sum of electricity produced
hourly_data['total'] = hourly_data[list(hourly_data.columns)].sum(axis=1)

# And changing column names to understand them more easily
hourly_data.columns = ['date', 'biomass', 'gas',
                       'coal', 'oil', 'solar', 'waste',  'wind', 'total']


# print(hourly_data.columns)
# print(hourly_data.head())

# Important note, I noticed that there is 1 additional value that should not be in the csv file,
# and during import of the data to the database it was confirmed
duplicate_indeces = hourly_data[hourly_data['date'].isin(
    hourly_data['date'][hourly_data['date'].duplicated()])]

# So, by looking at the data, it seemed like an error from the data source, and by deductions I will drop the second row,
# as first row is closer to values of nearby hours
hourly_data.drop(duplicate_indeces.index[0], axis=0, inplace=True)

# And lastly
# print(hourly_data.info())
# need to check why there is null value for one row
# finding that exact row
null_values = hourly_data[hourly_data.isnull().any(axis=1)]
null_index = null_values.index[0]

# i looked up for this row in excel datasheet and it seems like system error, and we either can omit the data or impute it
# for this task purposes, i believe it is a good idea to take average of nearby rows and assign those values to it,
# as at first glance it seems like there is trend of slightly increasing electricity production by hour at that time period
# For real life application, further and advanced research about this matter would be required
hourly_data.loc[null_index] = (hourly_data.loc[null_index -
                                               1, hourly_data.columns != 'date'].astype(int) / 2 + hourly_data.loc[null_index + 1, hourly_data.columns != 'date'].astype(int) / 2).astype(int)
hourly_data.loc[null_index, 'date'] = null_values['date'].item()

# Connecting/creating electricityMap database
conn = sqlite3.connect("db/electricityMap.db")
cursor = conn.cursor()

# Drop table if already exists
cursor.execute("DROP TABLE IF EXISTS production")


# Let's create sqlite table to store all these information
cursor.execute(
    """
    CREATE TABLE production (
        date TEXT NOT NULL,
        biomass INTEGER,
        gas INTEGER,
        coal INTEGER,
        oil INTEGER,
        solar INTEGER,
        waste INTEGER,
        wind INTEGER,
        total INTEGER,
        PRIMARY KEY(date)
        );
     """
)

hourly_data.to_sql('production', conn, if_exists='append', index=False)

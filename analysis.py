import pandas as pd
import numpy as np
import sqlite3
import json
import seaborn as sns
import matplotlib.pyplot as plt


# Display settings
pd.set_option('display.max_rows', 30)
pd.set_option('display.max_columns', 20)

# Connecting to electricityMap database
conn = sqlite3.connect("db/electricityMap.db")
cursor = conn.cursor()

# retrieving data from database
df = pd.read_sql("SELECT * FROM production", conn)

# retrieving carbon intensity per production type
file = open('co2eq_parameters.json')
carbon_intensity = json.load(file)
carbon_intensity = carbon_intensity['emissionFactors']['defaults']

# exploring data
# print(df.head())
# print(df.info())
# print(carbon_intensity)

# storing values of each production types that are within our hourly production dataset
carbon_intensity_list = []
for key, value in carbon_intensity.items():
    if key in df.columns:
        carbon_intensity_list.append(value['value'])

# I am not sure about carbon intensity of the waste production type, but from what I found it was the same as biomass, which is 240
carbon_intensity_list.insert(len(carbon_intensity_list) - 1, 240)

# print(carbon_intensity_list)

# calculating carbon intensity for each hour
df["carbon_intensity"] = np.ceil((
    df.iloc[:, 1:(len(df.columns) - 1)] * carbon_intensity_list).sum(axis=1) / df['total']).astype(int)

# calculating carbon intensity per each production type for each hour
# p.s I am ceiling the results becuase during some of my calculations with your live app version, it seemed like most of the values round up
# to higher int than lower. This function can easily be changed up to company's preference
for i in range(len(carbon_intensity_list)):
    df[df.columns[i+1] + "_intensity"] = np.ceil(
        df[df.columns[i+1]] * carbon_intensity_list[i] / df['total']).astype(int)

# change date string to datetime
df['date'] = pd.to_datetime(df['date'])

# extracting specific month/day/hour from datetime
df['month'] = pd.DatetimeIndex(df['date']).month
df['day_of_week'] = pd.DatetimeIndex(df['date']).day_name()
df['day'] = pd.DatetimeIndex(df['date']).day
df['hour'] = pd.DatetimeIndex(df['date']).hour

days_sort = ['Monday', 'Tuesday', 'Wednesday',
             'Thursday', 'Friday', 'Saturday', 'Sunday']

# avg carbon intensity by month/day/hour for visualization purposes
hour_avg = df.groupby(['hour'])['carbon_intensity'].mean()
day_of_week_avg = df.groupby(['day_of_week'])[
    'carbon_intensity'].mean().reindex(days_sort)
day_avg = df.groupby(['day'])['carbon_intensity'].mean()
month_avg = df.groupby(['month'])['carbon_intensity'].mean()

# avg total production by month/day/hour for visualization purposes
hour_avg_prod = df.groupby(['hour'])['total'].mean()
day_of_week_avg_prod = df.groupby(['day_of_week'])[
    'total'].mean().reindex(days_sort)
day_avg_prod = df.groupby(['day'])['total'].mean()
month_avg_prod = df.groupby(['month'])['total'].mean()

# plotting 4 different graphs with comparison of hourly/day_of_week/monthly carbon intensity vs how much electricity was produced
fig, ax = plt.subplots(1, 2)
sns.barplot(x=hour_avg.index, y=hour_avg.values, ax=ax[0]).set_title(
    "Avg Carbon Intensity by hour (gCo2/KWh)")
sns.barplot(x=hour_avg_prod.index, y=hour_avg_prod.values,
            ax=ax[1]).set_title("Avg total electricity production by hour (MW)")
plt.show()

fig, ax = plt.subplots(1, 2)
sns.barplot(x=day_of_week_avg.index, y=day_of_week_avg.values, ax=ax[0]).set_title(
    "Avg Carbon Intensity by day of the week (gCo2/KWh)")
sns.barplot(x=day_of_week_avg_prod.index, y=day_of_week_avg_prod.values,
            ax=ax[1]).set_title("Avg total electricity production by day of the week (MW)")
plt.show()

fig, ax = plt.subplots(1, 2)
sns.barplot(x=day_avg.index, y=day_avg.values, ax=ax[0]).set_title(
    "Avg Carbon Intensity by day of the month (gCo2/KWh)")
sns.barplot(x=day_avg_prod.index, y=day_avg_prod.values,
            ax=ax[1]).set_title("Avg total electricity production by day of the month (MW)")
plt.show()

fig, ax = plt.subplots(1, 2)
sns.barplot(x=month_avg.index, y=month_avg.values, ax=ax[0]).set_title(
    "Avg Carbon Intensity by month (gCo2/KWh)")
sns.barplot(x=month_avg_prod.index, y=month_avg_prod.values,
            ax=ax[1]).set_title("Avg total electricity production by month (MW)")
plt.show()

import sys
import os

# Add app folder to path so we can import database.py
sys.path.append(os.path.abspath('app'))

import pandas as pd
from database import load_analytics_data_v2

print("Loading data from warehouse...")
df_base = load_analytics_data_v2()
print(f"Columns in df_base: {df_base.columns.tolist()}")
print(f"Total records: {len(df_base)}")

df_filtered = df_base.copy()
total_records = len(df_filtered)
valid_records = df_filtered[df_filtered['is_valid'] == True]

print("Grouping by ['tahun_data', 'label_periode']...")
df_trend = valid_records.groupby(['tahun_data', 'label_periode']).agg(
    total_sampel=('status_exceed', 'count'),
    total_pelanggaran=('status_exceed', 'sum')
).reset_index()

df_trend['% Pelanggaran'] = (df_trend['total_pelanggaran'] / df_trend['total_sampel'] * 100).round(1)
df_trend = df_trend.sort_values(by=['tahun_data', 'label_periode'])

print("Dataframe grouped successfully:")
print(df_trend.head())

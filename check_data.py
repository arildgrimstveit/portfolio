import pandas as pd

# Load the data
df = pd.read_csv('data/portfolio.csv')

print("📊 Portfolio Data Analysis")
print("=" * 50)
print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
print(f"Total records: {len(df)}")

print("\n📈 Records per instrument:")
instrument_stats = df.groupby('Instrument')['Date'].agg(['count', 'min', 'max']).sort_values('count', ascending=False)
for instrument, stats in instrument_stats.iterrows():
    print(f"  {instrument}: {stats['count']} records from {stats['min']} to {stats['max']}")

print("\n🔍 Checking all instruments:")
for instrument in df['Instrument'].unique():
    instrument_data = df[df['Instrument'] == instrument].sort_values('Date')
    if len(instrument_data) > 0:
        print(f"  {instrument}: {len(instrument_data)} records from {instrument_data['Date'].min()} to {instrument_data['Date'].max()}")
        if len(instrument_data) <= 10:
            print(f"    Values: {instrument_data['Value_kNOK'].tolist()}")
    else:
        print(f"  {instrument}: NO DATA")

print(f"\n📅 Total unique instruments: {df['Instrument'].nunique()}")
print(f"📅 Instruments with data: {len([inst for inst in df['Instrument'].unique() if len(df[df['Instrument'] == inst]) > 0])}") 
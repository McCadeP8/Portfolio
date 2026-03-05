from pybaseball import statcast
import pandas as pd

# Pull all of 2025’s Statcast pitches
df_2025 = statcast(start_dt='2025-03-01', end_dt='2025-10-01')

print(df_2025.shape)  # ~700k+ rows
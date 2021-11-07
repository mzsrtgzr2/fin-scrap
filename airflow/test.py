

import pandas as pd
import vaex as va
from datetime import datetime
import numpy as np
def _gen():
    for i in range(100_000_000):
        if i%1000 == 0:
            print(i)
        yield i
stream = _gen()

print('loading')
# df = va.from_pandas(pd.DataFrame(stream))
df = va.from_arrays(x=np.array(_gen()))
dt = datetime(2021,10,1)
print('starting to write')
df.export_parquet(
    f's3://pc360-test-bucket4/'
    f'raw/trades/'
    f'trades__1.parquet',
    chunk_size=10,
    fs_options={
        'profile': 'integ_mrot'
    }
)

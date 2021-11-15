

Airflow should schedule a trades fetcher every couple of hours
we can't tell for sure it's going to be trades for a date
and even if yes for the same date it shoudl be incremental

offloading the trades should be to some file in s3 or kafka stream.
where we can eventually read the trades and do some compute. 

this is just one type of data, not all data is going to be small like the trades data.
maybe we will scrap textual input that will be big. i think that
puting it all in datalake is a better approach. zero limitations on size and 
we don't need it really as a stream now. 

later, if we use some real time computations can add kafka to this plot. 

trades read to an append-to csv file. than, we can move it to some dataware house.


## nov-15-21

### storage type
- need to move to parquet instead of csv, the storage is very big.
- need to move to partition by month to get bigger files.

### history fetching
fetcher direction - don't need really all the data of a stock, just for the last year will be enough. - start from today, and move backwards.

how am i going to do it?
- if we don't have marker - just fetch trades w/o fromId argument - we get the latest 1000 trades.
- take the very first id in the response
- fetch from (id-1001) and repeat
- pour results to the appropriate parquet file (partition by month)

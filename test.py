import re
from datetime import datetime, timedelta

pipe_settlement_period = '200 Days'

numeric_period = re.findall(r'\d+', pipe_settlement_period)



if numeric_period:
    settlement_period_value = int(numeric_period[0])
else:
    settlement_period_value = 0

# Calculate settlement date
currenct_datetime = datetime.now()
yesterday = currenct_datetime - timedelta(days=1)
transaction_date            = yesterday
transaction_settlement_date = transaction_date + timedelta(days=settlement_period_value)


print('settlement_period_value', settlement_period_value)
print('transaction_settlement_date', transaction_settlement_date)
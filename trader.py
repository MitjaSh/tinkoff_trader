from openapi_client import openapi
from datetime import datetime, timedelta
from pytz import timezone
import time

# according to tariff Trader commission = 0.05%+0.05%
global commission
commission = 0.001

def find_curve(candle_list, descent_perc = 2, advance_perc = 0.5):
    res = {}
    stage = 'Srart'
    for i in (sorted(candle_list, key=lambda d: getattr(d, 'time'), reverse=True)):
        if stage == 'Srart':
            res['current_value'] = getattr(i, 'c')
            stage = 'Advance'
        elif stage == 'Advance' and getattr(i, 'c') < res['current_value'] / 100 * (100 - advance_perc):
            res['low_value'] = getattr(i, 'c')
            res['low_time'] = getattr(i, 'time')
            stage = 'Descent'
        elif stage == 'Descent' and getattr(i, 'c') < res['low_value']:
            res['low_value'] = getattr(i, 'c')
            res['low_time'] = getattr(i, 'time')
        elif stage == 'Descent' and getattr(i, 'c') > res['current_value'] / 100 * (100 + descent_perc):
            res['high_value'] = getattr(i, 'c')
            res['high_time'] = getattr(i, 'time')
            stage = 'Found'
        elif stage == 'Found' and getattr(i, 'c') > res['high_value']:
            res['high_value'] = getattr(i, 'c')
            res['high_time'] = getattr(i, 'time')
    if stage == 'Found':
        return res

def log(message, file_name='log.txt'):
   f = open(file_name, 'a')
   f.write(datetime.now() + message + '\n')
   f.close()


f = open('token.txt', 'r')
token = f.read()
f.close()

client = openapi.sandbox_api_client(token)

mkt = client.market.market_stocks_get()
j = 0
time_to = datetime.now()
time_from = time_to + timedelta(days=-7)
fmt = '%Y-%m-%dT%H:%M:%S.%f+03:00'

for i in (getattr(getattr(mkt, 'payload'), 'instruments')):
    j = j + 1
    time.sleep(1)
##    if j > 10:
##        break
    response = client.market.market_candles_get(getattr(i, 'figi'),time_from.strftime(fmt),time_to.strftime(fmt),'hour')
    candles = getattr(getattr(response, 'payload'), 'candles')
    q = find_curve(candles)
    if q:
        print(getattr(i, 'ticker') + '\n' + str(q) + '\n' + str(j) + '\n\n')

#bought.txt

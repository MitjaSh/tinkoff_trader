from openapi_client import openapi
from datetime import datetime, timedelta
from pytz import timezone
import time

# according to tariff Trader commission = 0.05%+0.05%
global commission
commission = 0.001

def find_curve(candle_list, price, descent_perc = 2, advance_perc = 0.5):
    res = {}
    res['current_value'] = price
    stage = 'Advance'
    for i in (sorted(candle_list, key=lambda d: getattr(d, 'time'), reverse=True)):
        if stage == 'Advance' and getattr(i, 'c') < res['current_value'] / 100 * (100 - advance_perc):
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
   f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + str(message) + '\n')
   f.close()

def buy(figi, qty, currency, price):
    with open('bought.txt', 'a') as g:
            g.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + 
                   ' ' + str(figi).ljust(8, ' ') +
                   ' ' + str(qty).ljust(5, ' ') +
                   ' ' + str(currency).ljust(4, ' ') +
                   ' ' + str(price) + '\n')
    return price*qty

def get_bought():
    b = []
    with open('bought.txt', 'r') as f:
        for item in f:
            b.append({'time':datetime(int(item[0:4]), int(item[5:7]), int(item[8:10]), int(item[11:13]), int(item[14:16]), int(item[17:19])),
                      'figi':item[20:29].rstrip(),
                      'qty':int(item[29:35]),
                      'currency':item[35:38],
                      'price':float(item[40:].rstrip())
                      })
    return b


def sell(figi, qty, price):
    part_qty = 0
    bb = get_bought()
    with open('bought.txt', 'w') as f:
        for b in (bb):
            if b['figi'] == figi and b['qty'] <= qty-part_qty:
                part_qty = part_qty+b['qty']
                with open('sold.txt', 'a') as sf:
                    sf.write(b['time'].strftime('%Y-%m-%d %H:%M:%S') +
                            '  ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') +
                            ' ' + str(b['figi']).ljust(8, ' ') +
                            ' ' + str(b['qty']).ljust(5, ' ') +
                            ' ' + str(b['currency']).ljust(4, ' ') +
                            ' ' + str(b['price']).ljust(10, ' ') +
                            ' ' + str(price) + '\n')
            elif b['figi'] == figi:
                with open('sold.txt', 'a') as sf:
                    sf.write(b['time'].strftime('%Y-%m-%d %H:%M:%S') +
                            '  ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') +
                            ' ' + str(b['figi']).ljust(8, ' ') +
                            ' ' + str(qty-part_qty).ljust(5, ' ') +
                            ' ' + str(b['currency']).ljust(4, ' ') +
                            ' ' + str(b['price']).ljust(10, ' ') +
                            ' ' + str(price) + '\n')

                    f.write(b['time'].strftime('%Y-%m-%d %H:%M:%S') + 
                   ' ' + str(b['figi']).ljust(8, ' ') +
                   ' ' + str(b['qty']-qty+part_qty).ljust(5, ' ') +
                   ' ' + str(b['currency']).ljust(4, ' ') +
                   ' ' + str(b['price']) + '\n')
            else:
                    f.write(b['time'].strftime('%Y-%m-%d %H:%M:%S') + 
                   ' ' + str(b['figi']).ljust(8, ' ') +
                   ' ' + str(b['qty']).ljust(5, ' ') +
                   ' ' + str(b['currency']).ljust(4, ' ') +
                   ' ' + str(b['price']) + '\n')
                    
def update_balance(amount, currency):
    b = {}
    try:
        f = open('balances.txt', 'r')
        for line in f:
            b[line[0:3]] = line[4:].strip()
        f.close()
    except FileNotFoundError:
        b['RUR'] = 0
        b['USD'] = 0
        b['EUR'] = 0
    try:
        b[currency] = round(float(b[currency]) + amount, 2)
    except KeyError:
        b[currency] = amount

    with open('balances.txt', 'w') as g:
        for curr in b.keys():
            g.write(curr + '=')
            g.write(str(b[curr])+'\n')
    return b[currency]

##buy('YDNX', 3, 'RUR', 99.13)
##buy('GASD', 1, 'USD', 0.123)
##print(buy('BO', 200, 'EUR', 125.4))
##print(buy('BO', 100, 'EUR', 123.4))
##print(sell('BO', 250, 127.4))


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
    if j > 10:
        break
    response = client.market.market_orderbook_get(getattr(i, 'figi'), 2)
    
    if getattr(getattr(response, 'payload'), 'trade_status') != 'NormalTrading':
        print(response)
        continue
    # The Cheapest offer in orderbook
    price = float(getattr(getattr(getattr(response, 'payload'), 'asks')[0], 'price'))
    if not price:
        print(response + '\n\n')
        continue
    
    response = client.market.market_candles_get(getattr(i, 'figi'),time_from.strftime(fmt),time_to.strftime(fmt),'hour')
    candles = getattr(getattr(response, 'payload'), 'candles')
    q = find_curve(candles, price)
    if q:
        buy(getattr(i, 'figi'), 1, getattr(i, 'currency'), price)
        print(getattr(i, 'ticker') + '\n' + str(q) + '\n' + str(j) + '\n\n')
		
		
if 'BO2' in [c['figi'] for c in get_bought()]:
  print('Yes')
else:
  print('No')

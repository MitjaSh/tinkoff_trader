from openapi_client import openapi
from datetime import datetime, timedelta
from pytz import timezone
import time

# according to tariff Trader commission = 0.05%+0.05%
global g_commission, g_profit
g_commission = 0.0005
g_profit = 0.01

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
   f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S')+ '  ' + str(message) + '\n')
   f.close()

def buy(ticker, figi, qty, currency, price):
    with open('bought.txt', 'a') as g:
            g.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S') + 
                   ' ' + str(ticker).ljust(12, ' ') +
                   ' ' + str(figi).ljust(12, ' ') +
                   ' ' + str(qty).ljust(5, ' ') +
                   ' ' + str(currency).ljust(4, ' ') +
                   ' ' + str(price) + '\n')
    return price*qty

def get_bought():
    b = []
    with open('bought.txt', 'r') as f:
        for item in f:
            b.append({'time':datetime(int(item[0:4]), int(item[5:7]), int(item[8:10]), int(item[11:13]), int(item[14:16]), int(item[17:19])),
                      'ticker':item[20:33].rstrip(),
                      'figi':item[33:46].rstrip(),
                      'qty':int(item[46:52]),
                      'currency':item[52:55],
                      'price':float(item[57:].rstrip())
                      })
    return b


def sell(ticker, qty, price):
    part_qty = 0
    bb = get_bought()
    with open('bought.txt', 'w') as f:
        for b in (bb):
            if b['ticker'] == ticker and b['qty'] <= qty-part_qty:
                part_qty = part_qty+b['qty']
                with open('sold.txt', 'a') as sf:
                    sf.write(b['time'].strftime('%Y-%m-%d %H:%M:%S') +
                            '  ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') +
                            ' ' + str(b['ticker']).ljust(12, ' ') +
                            ' ' + str(b['figi']).ljust(12, ' ') +
                            ' ' + str(b['qty']).ljust(5, ' ') +
                            ' ' + str(b['currency']).ljust(4, ' ') +
                            ' ' + str(b['price']).ljust(10, ' ') +
                            ' ' + str(price).ljust(10, ' ') +
                            ' ' + str(round((price*b['qty']*(1-g_commission)) - (b['price']*b['qty']*(1+g_commission)),2)) # Profit
                                + '\n')
            elif b['ticker'] == ticker:
                with open('sold.txt', 'a') as sf:
                    if qty-part_qty != 0:
                        sf.write(b['time'].strftime('%Y-%m-%d %H:%M:%S') +
                                '  ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') +
                                ' ' + str(b['ticker']).ljust(12, ' ') +
                                ' ' + str(b['figi']).ljust(12, ' ') +
                                ' ' + str(qty-part_qty).ljust(5, ' ') +
                                ' ' + str(b['currency']).ljust(4, ' ') +
                                ' ' + str(b['price']).ljust(10, ' ') +
                                ' ' + str(price).ljust(10, ' ') +
                                ' ' + str(round((price*(qty-part_qty)*(1-g_commission)) - (b['price']*(qty-part_qty)*(1+g_commission)),2))  # Profit
                                    + '\n')

                    f.write(b['time'].strftime('%Y-%m-%d %H:%M:%S') + 
                   ' ' + str(b['ticker']).ljust(12, ' ') +
                   ' ' + str(b['figi']).ljust(12, ' ') +
                   ' ' + str(b['qty']-qty+part_qty).ljust(5, ' ') +
                   ' ' + str(b['currency']).ljust(4, ' ') +
                   ' ' + str(b['price']) + '\n')
                    part_qty = qty
            else:
                    f.write(b['time'].strftime('%Y-%m-%d %H:%M:%S') + 
                   ' ' + str(b['ticker']).ljust(12, ' ') +
                   ' ' + str(b['figi']).ljust(12, ' ') +
                   ' ' + str(b['qty']).ljust(5, ' ') +
                   ' ' + str(b['currency']).ljust(4, ' ') +
                   ' ' + str(b['price']) + '\n')
    return part_qty
	
                    
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
	
def get_balance(currency):
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
    return b[currency]

def find_and_buy():
    f = open('token.txt', 'r')
    token = f.read()
    f.close()

    client = openapi.sandbox_api_client(token)
    mkt = client.market.market_stocks_get()
    j = 0
    time_to = datetime.now()
    time_from = time_to + timedelta(days=-1)
    fmt = '%Y-%m-%dT%H:%M:%S.%f+03:00'

    bought_qty = 0
    
    for i in (getattr(getattr(mkt, 'payload'), 'instruments')):
        try:    
            if getattr(i, 'ticker') in [c['ticker'] for c in get_bought()]:
                print(getattr(i, 'ticker') + ' already bought\n')
                continue
        except FileNotFoundError:
            None
            
        j = j + 1
        time.sleep(1)
##        if j > 100:
##            break
        try:
            response = client.market.market_orderbook_get(getattr(i, 'figi'), 2)
        except Exception as err:
            print(getattr(i, 'ticker') + '\n' + str(err))
            continue
        
        if getattr(getattr(response, 'payload'), 'trade_status') != 'NormalTrading':
            print(getattr(i, 'ticker') + ' ' + getattr(getattr(response, 'payload'), 'trade_status')+ '\n')
            continue
        # The Cheapest offer in orderbook
        try:
            price = float(getattr(getattr(getattr(response, 'payload'), 'asks')[0], 'price'))
        except IndexError:
            print('IndexError: list index out of range')
            print(getattr(i, 'ticker') + ' ' + str(response) + '\n')
            continue
        if not price:
            print('No price')
            print(str(response) + '\n')
            continue

        if (price>100 and getattr(i, 'currency') in ['USD','EUR']) or (price>5000 and getattr(i, 'currency') == 'RUB'):
            print(getattr(i, 'ticker') + ' ' + str(price) + getattr(i, 'currency') + ' Too expensive\n')
            continue
			
        if price>float(get_balance(getattr(i, 'currency'))):
            print(getattr(i, 'ticker') + ' ' + str(price) + getattr(i, 'currency') + ' Not enough money\n')
            continue
     
        try:
            response = client.market.market_candles_get(getattr(i, 'figi'),time_from.strftime(fmt),time_to.strftime(fmt),'10min')
        except Exception as err:
            print(getattr(i, 'ticker') + '\n' + str(err))
            continue
            
        candles = getattr(getattr(response, 'payload'), 'candles')
        q = find_curve(candles, price, 3, 1)
        if q:
            current_qty = 1
            buy(getattr(i, 'ticker'), getattr(i, 'figi'), current_qty, getattr(i, 'currency'), price)
            update_balance(-1*current_qty*price, getattr(i, 'currency'))
            bought_qty = bought_qty+current_qty
            log(getattr(i, 'ticker') + ' ' + str(q) + '\n')
        with open('delete_to_stop.txt', 'r') as stp_file:
            None
    return bought_qty

def check_and_sell(profit):
    f = open('token.txt', 'r')
    token = f.read()
    f.close()

    total_sold_qty = 0
    
    client = openapi.sandbox_api_client(token)
    
    for stock in get_bought():
        response = client.market.market_orderbook_get(stock['figi'], 2)
        try:
            price = float(getattr(getattr(getattr(response, 'payload'), 'bids')[0], 'price'))
        except IndexError:
            print('IndexError: list index out of range')
            print(stock['ticker'] + ' ' + str(response) + '\n')
            continue

        if stock['price']*(1+g_commission)*(1+g_profit) <= price*(1-g_commission):
            sold_qty = sell(stock['ticker'], stock['qty'], price)
            total_sold_qty = total_sold_qty + sold_qty
            print(stock['ticker'] + ' sold ' + str(stock['price']) + ' ' + str(price))
            update_balance(sold_qty*price, stock['currency'])
        time.sleep(1)
    return total_sold_qty






##print(buy('YDNX56789012', 'BBG000BLNQ14', 3, 'RUR', 1.0013))
##print(buy('GASD', 'BBG000BLNQ15', 1, 'USD', 0.123))
##print(buy('BO', 'BBG000BLNQ16', 200, 'EUR', 125.4))
##print(buy('BO', 'BBG000BLNQ16', 110, 'EUR', 123.4))
##print(sell('YDNX56789012', 2, 1.0024))
##print(sell('BO', 150, 1.0024))
#update_balance(1500, 'USD')
#time.sleep(60*140)
with open('delete_to_stop.txt', 'w') as stp_file:
    stp_file.write(str(datetime.now())+'\n')

while 2 > 1:
    with open('delete_to_stop.txt', 'r') as stp_file:
        None
    if float(get_balance('USD'))<1 and float(get_balance('EUR'))<1 and float(get_balance('RUB'))<50: #No money left
        print('No money left\n\n')
        time.sleep(60*5)
    log('find_and_buy=' + str(find_and_buy()))
    log('check_and_sell=' + str(check_and_sell(g_profit)))

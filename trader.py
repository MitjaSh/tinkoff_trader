from openapi_client import openapi
from datetime import datetime, timedelta
from pytz import timezone
import time
import os

global g_trial, g_params, g_trial_params, client, g_fmt, g_not_available, g_stock_price

def check_find_curve(figi, v_days, period, price, descent_perc = 2, advance_perc = 0.5):
    time_to = datetime.now()
    time_from = time_to + timedelta(days=-1 * v_days)    

    try:
        response = client.market.market_candles_get(figi,time_from.strftime(g_fmt),time_to.strftime(g_fmt),period)
    except Exception as err:
        output(figi + ' ' + str(err))
        log(figi + ' ' + str(err))
        return None

        
    candles = getattr(getattr(response, 'payload'), 'candles')
    
    res = {}
    res['current_value'] = price
    stage = 'Advance'
    for i in (sorted(candles, key=lambda d: getattr(d, 'time'), reverse=True)):
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

def should_i_stop():
    with open('delete_to_stop.txt', 'r') as stp_file:
        None

def log(message, file_name='log.txt'):
    f = open(file_name, 'a')
    if file_name =='log.txt':
        try:
            trial_str = g_trial + '  '
        except NameError:
            trial_str = ''
    else:
        trial_str = ''
    f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S')+ '  ' + trial_str + str(message) + '\n')
    f.close()
    print(trial_str + str(message))

def output(message):
    print(g_trial + ' ' + str(message))

def buy(ticker, figi, qty, currency, price):
    with open(g_trial + '/bought.txt', 'a') as g:
            g.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S') +
                   ' ' + str(ticker).ljust(12, ' ') +
                   ' ' + str(figi).ljust(12, ' ') +
                   ' ' + str(qty).ljust(5, ' ') +
                   ' ' + str(currency).ljust(4, ' ') +
                   ' ' + str(price) + '\n')
    return price*qty

def get_bought():
    b = []
    try:
        with open(g_trial + '/bought.txt', 'r') as f:
            for item in f:
                b.append({'time':datetime(int(item[0:4]), int(item[5:7]), int(item[8:10]), int(item[11:13]), int(item[14:16]), int(item[17:19])),
                          'ticker':item[20:33].rstrip(),
                          'figi':item[33:46].rstrip(),
                          'qty':int(item[46:52]),
                          'currency':item[52:55],
                          'price':float(item[57:].rstrip())
                          })
    except FileNotFoundError:
        return b
    return b


def sell(ticker, qty, price):
    part_qty = 0
    bb = get_bought()
    with open(g_trial + '/bought.txt', 'w') as f:
        for b in (bb):
            if b['ticker'] == ticker and b['qty'] <= qty-part_qty:
                part_qty = part_qty+b['qty']
                with open(g_trial + '/sold.txt', 'a') as sf:
                    sf.write(b['time'].strftime('%Y-%m-%d %H:%M:%S') +
                            '  ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') +
                            ' ' + str(b['ticker']).ljust(12, ' ') +
                            ' ' + str(b['figi']).ljust(12, ' ') +
                            ' ' + str(b['qty']).ljust(5, ' ') +
                            ' ' + str(b['currency']).ljust(4, ' ') +
                            ' ' + str(b['price']).ljust(10, ' ') +
                            ' ' + str(price).ljust(10, ' ') +
                            ' ' + str(round((price*b['qty']*(1-float(g_trial_params['COMMISSION']))) - (b['price']*b['qty']*(1+float(g_trial_params['COMMISSION']))),2)) # Profit
                                + '\n')
            elif b['ticker'] == ticker:
                with open(g_trial + '/sold.txt', 'a') as sf:
                    if qty-part_qty != 0:
                        sf.write(b['time'].strftime('%Y-%m-%d %H:%M:%S') +
                                '  ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') +
                                ' ' + str(b['ticker']).ljust(12, ' ') +
                                ' ' + str(b['figi']).ljust(12, ' ') +
                                ' ' + str(qty-part_qty).ljust(5, ' ') +
                                ' ' + str(b['currency']).ljust(4, ' ') +
                                ' ' + str(b['price']).ljust(10, ' ') +
                                ' ' + str(price).ljust(10, ' ') +
                                ' ' + str(round((price*(qty-part_qty)*(1-float(g_trial_params['COMMISSION']))) - (b['price']*(qty-part_qty)*(1+float(g_trial_params['COMMISSION']))),2))  # Profit
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

def get_sold():
    b = []
    try:
        with open(g_trial + '/sold.txt', 'r') as f:
            for item in f:
                b.append({'time':datetime(int(item[0:4]), int(item[5:7]), int(item[8:10]), int(item[11:13]), int(item[14:16]), int(item[17:19])),
                          'ticker':item[41:54].rstrip(),
                          'figi':item[54:67].rstrip(),
                          'qty':int(item[67:73]),
                          'currency':item[73:76],
                          'profit':float(item[100:].rstrip())
                          })
    except FileNotFoundError:
        return b
    return b

def print_dict(v_dict, prefix = ''):
    res = ''
    for i in sorted(list(v_dict.keys())):
        res = res + prefix + str(i) + ': ' + str(v_dict[i]) + '\n'
    return res

def update_balance(amount, currency):
    b = {}
    try:
        f = open(g_trial+'/balances.txt', 'r')
        for line in f:
            b[line[0:3]] = line[4:].strip()
        f.close()
    except FileNotFoundError:
        b['RUB'] = 0
        b['USD'] = 0
        b['EUR'] = 0
    try:
        b[currency] = round(float(b[currency]) + amount, 2)
    except KeyError:
        b[currency] = amount

    with open(g_trial+'/balances.txt', 'w') as g:
        for curr in b.keys():
            g.write(curr + '=')
            g.write(str(b[curr])+'\n')
    return b[currency]

def get_balance(currency):
    b = {}
    try:
        f = open(g_trial+'/balances.txt', 'r')
        for line in f:
            b[line[0:3]] = line[4:].strip()
        f.close()
    except FileNotFoundError:
        b['RUB'] = 0
        b['USD'] = 0
        b['EUR'] = 0
    return b[currency]

def get_statistic():
    b = {}
    try:
        f = open(g_trial+'/balances.txt', 'r')
        for line in f:
            b['Balance ' + line[0:3]] = line[4:].strip()
        f.close()
    except FileNotFoundError:
        b['Balance RUB'] = 0
        b['Balance USD'] = 0
        b['Balance EUR'] = 0
    b['Bought RUB'] = 0
    b['Bought USD'] = 0
    b['Bought EUR'] = 0
    for i in (get_bought()):
        b['Bought '+i['currency']] = b['Bought '+i['currency']] + i['price'] * i['qty']
    b['Balance&Bought RUB'] = float(b['Balance RUB']) + float(b['Bought RUB'])
    b['Balance&Bought USD'] = float(b['Balance USD']) + float(b['Bought USD'])
    b['Balance&Bought EUR'] = float(b['Balance EUR']) + float(b['Bought EUR'])
    b['Profit RUB'] = 0
    b['Profit USD'] = 0
    b['Profit EUR'] = 0
    for i in (get_sold()):
        b['Profit '+i['currency']] = b['Profit '+i['currency']] + i['profit']
    return b

def update_statistic (stat_dict, event, qty=1):
    try:
        stat_dict[event] = stat_dict[event] + qty
    except KeyError:
        stat_dict[event] = qty
    return stat_dict

def find_and_buy():
    mkt = client.market.market_stocks_get()
    result_statistic = {}
    bought_list = get_bought()
    result_statistic['Go to checks'] = 0
    # Cycle on stocks
    for i in (getattr(getattr(mkt, 'payload'), 'instruments')):
        should_i_stop()
        update_statistic(result_statistic, 'Total')
        
        # Check for already requested and bought
        if getattr(i, 'ticker') in [c['ticker'] for c in bought_list]:
            output(getattr(i, 'ticker') + ' already bought')
            update_statistic(result_statistic, 'Already bought')
            continue
        
        #Past experienced checks
        if getattr(i, 'ticker') in g_not_available:
            output(getattr(i, 'ticker') + ' NotAvailableForTrading (Past experience)')
            update_statistic(result_statistic, 'NotAvailableForTrading (Past experience)')
            continue

        try:
            if (g_stock_price[getattr(i, 'ticker')] > float(g_trial_params['EXPENSIVE_USD']) and getattr(i, 'currency') in ['USD','EUR']) \
                    or (g_stock_price[getattr(i, 'ticker')] > float(g_trial_params['EXPENSIVE_RUB']) and getattr(i, 'currency') == 'RUB'):
                output(getattr(i, 'ticker') + ' Too expensive ' + getattr(i, 'currency') + ' (Past experience)')
                update_statistic(result_statistic, 'Too expensive ' + getattr(i, 'currency') + ' (Past experience)')
                continue
        except KeyError:
            None
        
        # After all offline checks: one pause every four processed stocks
        if result_statistic['Total'] % 4 == 0: #TBD Go to checks
            time.sleep(1)
                
        try:
            response = client.market.market_orderbook_get(getattr(i, 'figi'), 2)
        except Exception as err:
            output(getattr(i, 'ticker') + ' ' + str(err))
            log(getattr(i, 'ticker') + ' ' + str(err))
            update_statistic(result_statistic, 'Error')
            continue

        if getattr(getattr(response, 'payload'), 'trade_status') != 'NormalTrading':
            output(getattr(i, 'ticker') + ' ' + getattr(getattr(response, 'payload'), 'trade_status'))
            update_statistic(result_statistic, getattr(getattr(response, 'payload'), 'trade_status'))
            if getattr(getattr(response, 'payload'), 'trade_status') == 'NotAvailableForTrading':
                g_not_available.append(getattr(i, 'ticker'))
            continue
        
        # The Cheapest offer in orderbook
        try:
            price = float(getattr(getattr(getattr(response, 'payload'), 'asks')[0], 'price'))
            g_stock_price[getattr(i, 'ticker')] = price
        except IndexError:
            output('IndexError: list index out of range')
            print(getattr(i, 'ticker') + ' ' + str(response))
            update_statistic(result_statistic, 'IndexError: list index out of range')
            continue
        
        if not price:
            output('No price')
            print(str(response))
            update_statistic(result_statistic, 'No price')
            continue

        if (price > float(g_trial_params['EXPENSIVE_USD']) and getattr(i, 'currency') in ['USD','EUR']) \
                    or (price > float(g_trial_params['EXPENSIVE_RUB']) and getattr(i, 'currency') == 'RUB'):
            output(getattr(i, 'ticker') + ' ' + str(price) + getattr(i, 'currency') + ' Too expensive')
            update_statistic(result_statistic, 'Too expensive ' + getattr(i, 'currency'))
            continue
        
        if price>float(get_balance(getattr(i, 'currency'))):
            output(getattr(i, 'ticker') + ' ' + str(price) + getattr(i, 'currency') + ' Not enough money')
            update_statistic(result_statistic, 'Not enough money')
            continue

        # Apply checks
        update_statistic(result_statistic, 'Go to checks')
        with open(g_trial+'/check_curve.txt', 'r') as check_file:
            check_params = {line.split('=')[0] : line.split('=')[1].strip() for line in check_file}
            q = check_find_curve(getattr(i, 'figi'),
                                 int(check_params['DAYS']),
                                 check_params['PERIOD'],
                                 price,
                                 int(check_params['DESCENT_PERC']),
                                 int(check_params['ADVANCE_PERC']))
        if q:
            current_qty = 1
            buy(getattr(i, 'ticker'), getattr(i, 'figi'), current_qty, getattr(i, 'currency'), price)
            update_balance(-1*current_qty*price, getattr(i, 'currency'))
            log(getattr(i, 'ticker') + ' ' + str(q) + '\n', g_trial+'/log.txt')
            update_statistic(result_statistic, 'Bought events')
            update_statistic(result_statistic, 'Bought stocks', current_qty)
    return result_statistic

def check_and_sell(profit):
    total_sold_qty = 0

    for stock in get_bought():
        try:
            response = client.market.market_orderbook_get(stock['figi'], 2)
        except Exception as err:
            output(stock['ticker'] + ' ' + str(err))
            log(stock['ticker'] + ' ' + str(err))
            continue
        try:
            price = float(getattr(getattr(getattr(response, 'payload'), 'bids')[0], 'price'))
        except IndexError:
            output('IndexError: list index out of range')
            print(stock['ticker'] + ' ' + str(response) + '\n')
            continue

        if stock['price']*(1+float(g_trial_params['COMMISSION']))*(1+float(g_trial_params['PROFIT'])) <= \
           price*(1-float(g_trial_params['COMMISSION'])):
            sold_qty = sell(stock['ticker'], stock['qty'], price)
            total_sold_qty = total_sold_qty + sold_qty
            output(stock['ticker'] + ' sold ' + str(stock['price']) + ' ' + str(price))
            update_balance(sold_qty * price -
                           sold_qty * stock['price'] * float(g_trial_params['COMMISSION']) -
                           sold_qty * price * float(g_trial_params['COMMISSION'])
                           , stock['currency'])
        time.sleep(1)
    return total_sold_qty

def request(ticker, figi, qty, currency, price, req_type):
    with open(g_trial + '/request.txt', 'a') as g:
            g.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S') +
                   ' ' + str(ticker).ljust(12, ' ') +
                   ' ' + str(figi).ljust(12, ' ') +
                   ' ' + str(qty).ljust(5, ' ') +
                   ' ' + str(currency).ljust(4, ' ') +
                   ' ' + str(price).ljust(10, ' ') +
                   ' ' + req_type + '\n')
    return price*qty


def get_request():
    b = []
    try:
        with open(g_trial + '/request.txt', 'r') as f:
            for item in f:
                b.append({'time':datetime(int(item[0:4]), int(item[5:7]), int(item[8:10]), int(item[11:13]), int(item[14:16]), int(item[17:19])),
                          'ticker':item[20:33].rstrip(),
                          'figi':item[33:46].rstrip(),
                          'qty':int(item[46:52]),
                          'currency':item[52:55],
                          'price':float(item[57:68].rstrip()),
                          'type':item[68:].rstrip()
                          })
    except FileNotFoundError:
        return b
    return b


def check_requests():
    for r in get_request():
        if r['type'] == 'BUY':
            buy_qty = r['qty']
            print('BUY' + str(r['time']))
        elif r['type'] == 'SELL':
            sell_qty = r['qty']
            print('SELL' + str(r['time']))


with open('delete_to_stop.txt', 'w') as stp_file:
    stp_file.write(str(datetime.now())+'\n')
with open('trials.txt', 'r') as trials_file:
    trials = [line.strip() for line in trials_file]
# Reading common parameters
try:
    with open('params.txt', 'r') as params_file:
        g_params = {line.split('=')[0] : line.split('=')[1].strip() for line in params_file}
except FileNotFoundError:
    with open('params.txt', 'w') as params_file:
        params_file.write('PARAM=VALUE')
    print('params.txt created')
    exit(0)
last_iteration_start_time = datetime(2019, 12, 21, 15, 33, 0)
log('Starting')
f = open('token.txt', 'r')
token = f.read()
f.close()
#Sandbox or PROD
client = openapi.sandbox_api_client(token)
g_fmt = '%Y-%m-%dT%H:%M:%S.%f+03:00'
g_not_available = []
g_stock_price = {}
while 2 > 1:
    # No work at night
    if datetime.now().hour < int(g_params['START_TIME']):
        print('No work at night')
        time.sleep(60)
        should_i_stop()
        continue

    # Wait for time gap
    sec_between = (datetime.now() - last_iteration_start_time).total_seconds()
    if sec_between < int(g_params['TIME_GAP'])*60:
        should_i_stop()
        print('Pause for ' + str(int(g_params['TIME_GAP'])*60 - sec_between) + ' sec.')
        time.sleep(60)
        continue
    last_iteration_start_time = datetime.now()
    # Process trials
    for trial in trials:
        g_trial = trial
        should_i_stop()
        # Reading common parameters
        with open('params.txt', 'r') as params_file:
            g_params = {line.split('=')[0] : line.split('=')[1].strip() for line in params_file}
        # Reading trial parameters
        if not os.path.exists(trial): os.makedirs(trial)
        try:
            with open(trial+'/trial_params.txt', 'r') as trial_params_file:
                g_trial_params = {line.split('=')[0] : line.split('=')[1].strip() for line in trial_params_file}
        except FileNotFoundError:
            with open(trial+'/trial_params.txt', 'w') as trial_params_file:
                trial_params_file.write('PARAM=VALUE')
            output('trial_params.txt created')
            continue
        if float(get_balance('USD'))<1 and float(get_balance('EUR'))<1 and float(get_balance('RUB'))<50:
            output('No money left')
        elif datetime.now().hour < int(g_params['START_BUY_TIME']):
            print('We are not buying in the morning')
            g_not_available = []
            g_stock_price = {}
        else:
            log('\n' + print_dict(find_and_buy(), '                       '))
        log('check_and_sell=' + str(check_and_sell(g_trial_params['PROFIT'])))
        log('\n' + print_dict(get_statistic(), '                     '))

from openapi_client import openapi
from datetime import datetime, timedelta
from pytz import timezone
import time
import os



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

def buy(ticker, figi, lot_qty, lot, currency, price):
    with open(g_trial + '/bought.txt', 'a') as g:
            g.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S') +
                   ' ' + str(ticker).ljust(12, ' ') +
                   ' ' + str(figi).ljust(12, ' ') +
                   ' ' + str(lot_qty).ljust(5, ' ') +
                   ' ' + str(lot).ljust(6, ' ') +
                   ' ' + str(currency).ljust(4, ' ') +
                   ' ' + str(price) + '\n')
    return price*lot_qty*lot

def get_bought():
    b = []
    try:
        with open(g_trial + '/bought.txt', 'r') as f:
            for item in f:
                b.append({'time':datetime(int(item[0:4]), int(item[5:7]), int(item[8:10]), int(item[11:13]), int(item[14:16]), int(item[17:19])),
                          'ticker':item[20:33].rstrip(),
                          'figi':item[33:46].rstrip(),
                          'lot_qty':int(float(item[46:52])),
                          'lot':int(item[52:59]),
                          'currency':item[59:62],
                          'price':float(item[64:].rstrip())
                          })
    except FileNotFoundError:
        return b
    return b


def sell(ticker, lot_qty, price):
    part_qty = 0
    bb = get_bought()
    with open(g_trial + '/bought.txt', 'w') as f:
        for b in (bb):
            if b['ticker'] == ticker and b['lot_qty'] <= lot_qty-part_qty:
                part_qty = part_qty+b['lot_qty']
                with open(g_trial + '/sold.txt', 'a') as sf:
                    sf.write(b['time'].strftime('%Y-%m-%d %H:%M:%S') +
                            '  ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') +
                            ' ' + str(b['ticker']).ljust(12, ' ') +
                            ' ' + str(b['figi']).ljust(12, ' ') +
                            ' ' + str(b['lot_qty']).ljust(5, ' ') +
                            ' ' + str(b['lot']).ljust(6, ' ') +
                            ' ' + str(b['currency']).ljust(4, ' ') +
                            ' ' + str(b['price']).ljust(10, ' ') +
                            ' ' + str(price).ljust(10, ' ') +
                            ' ' + str(round((price*b['lot_qty']*b['lot']*(1-float(g_trial_params['COMMISSION']))) - (b['price']*b['lot_qty']*b['lot']*(1+float(g_trial_params['COMMISSION']))),2)) # Profit
                                + '\n')
            elif b['ticker'] == ticker:
                with open(g_trial + '/sold.txt', 'a') as sf:
                    if lot_qty-part_qty != 0:
                        sf.write(b['time'].strftime('%Y-%m-%d %H:%M:%S') +
                                '  ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') +
                                ' ' + str(b['ticker']).ljust(12, ' ') +
                                ' ' + str(b['figi']).ljust(12, ' ') +
                                ' ' + str(lot_qty-part_qty).ljust(5, ' ') +
                                ' ' + str(b['lot']).ljust(6, ' ') +
                                ' ' + str(b['currency']).ljust(4, ' ') +
                                ' ' + str(b['price']).ljust(10, ' ') +
                                ' ' + str(price).ljust(10, ' ') +
                                ' ' + str(round((price*(lot_qty-part_qty)*b['lot']*(1-float(g_trial_params['COMMISSION']))) - (b['price']*(lot_qty-part_qty)*b['lot']*(1+float(g_trial_params['COMMISSION']))),2))  # Profit
                                    + '\n')

                    f.write(b['time'].strftime('%Y-%m-%d %H:%M:%S') +
                   ' ' + str(b['ticker']).ljust(12, ' ') +
                   ' ' + str(b['figi']).ljust(12, ' ') +
                   ' ' + str(b['lot_qty']-lot_qty+part_qty).ljust(5, ' ') +
                   ' ' + str(b['lot']).ljust(6, ' ') +
                   ' ' + str(b['currency']).ljust(4, ' ') +
                   ' ' + str(b['price']) + '\n')
                    part_qty = lot_qty
            else:
                    f.write(b['time'].strftime('%Y-%m-%d %H:%M:%S') +
                   ' ' + str(b['ticker']).ljust(12, ' ') +
                   ' ' + str(b['figi']).ljust(12, ' ') +
                   ' ' + str(b['lot_qty']).ljust(5, ' ') +
                   ' ' + str(b['lot']).ljust(6, ' ') +
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
                          'lot_qty':int(item[67:73]),
                          'lot':int(item[73:80]),
                          'currency':item[80:83],
                          'profit':float(item[103:].rstrip())
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
        b['Bought '+i['currency']] = b['Bought '+i['currency']] + i['price'] * i['lot_qty']* i['lot']
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
    result_statistic = {}
    try:
        mkt = client.market.market_stocks_get()
    except Exception as err:
        output('Can''t ger stocks list: ' + str(err))
        log('Can''t ger stocks list: ' + str(err))
        return result_statistic
    
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
        if getattr(i, 'ticker') in [c['ticker'] for c in get_request()]:
            output(getattr(i, 'ticker') + ' already requested')
            update_statistic(result_statistic, 'Already requested')
            continue
        # Check for my portfolio
        try:
            response = client.portfolio.portfolio_get()
        except Exception as err:
            output(getattr(i, 'ticker') + ' ' + str(err))
            log(getattr(i, 'ticker') + ' ' + str(err))
            update_statistic(result_statistic, 'Error')
            continue
        
        if getattr(i, 'figi') in [getattr(c, 'figi') for c in getattr(getattr(response, 'payload'), 'positions')]:
            output(getattr(i, 'ticker') + ' in my investment portfolio')
            update_statistic(result_statistic, 'In my investment portfolio')
            continue
        
        #Past experienced checks
##        if getattr(i, 'ticker') in g_not_available:
##            output(getattr(i, 'ticker') + ' NotAvailableForTrading (Past experience)')
##            update_statistic(result_statistic, 'NotAvailableForTrading (Past experience)')
##            continue

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

        lot_qty = 1
        lot = int(getattr(i, 'lot'))
        # The Cheapest offer in orderbook
        try:
            price = float(getattr(getattr(getattr(response, 'payload'), 'asks')[0], 'price'))
            g_stock_price[getattr(i, 'ticker')] = price*lot
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

        if (price * lot > float(g_trial_params['EXPENSIVE_USD']) and getattr(i, 'currency') in ['USD','EUR']) \
                    or (price * lot > float(g_trial_params['EXPENSIVE_RUB']) and getattr(i, 'currency') == 'RUB'):
            output(getattr(i, 'ticker') + ' ' + str(price) + '*' + str(lot) + ' ' + getattr(i, 'currency') + ' Too expensive')
            update_statistic(result_statistic, 'Too expensive ' + getattr(i, 'currency'))
            continue

        if price * lot > float(get_balance(getattr(i, 'currency'))):
            output(getattr(i, 'ticker') + ' ' + str(price) + '*' + str(lot) + ' ' + getattr(i, 'currency') + ' Not enough money')
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
            requested_qty = request(getattr(i, 'ticker'), getattr(i, 'figi'), lot_qty, lot, getattr(i, 'currency'), price, 'Buy')
            if requested_qty > 0:
                log('Request to buy: ' + getattr(i, 'ticker') + ' ' + str(q) + '\n', g_trial+'/log.txt')
                update_statistic(result_statistic, 'Buy requests events')
                update_statistic(result_statistic, 'Buy requests stocks', requested_qty)
                # Update balance before request execution
                update_balance(-1*lot_qty*lot*price, getattr(i, 'currency'))
    return result_statistic

def check_and_sell(profit):
    result_statistic = {}

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
            requested_qty = request(stock['ticker'], stock['figi'], stock['lot_qty'], stock['lot'], stock['currency'], stock['price'], 'Sell', price)
            if requested_qty > 0:
                log('Request to sell: ' + stock['ticker'] + ' ' + str(stock['price']) + ' ' + str(price), g_trial+'/log.txt')
                update_statistic(result_statistic, 'Sell requests events')
                update_statistic(result_statistic, 'Sell requests stocks', requested_qty)
        time.sleep(1)
    return result_statistic

def request(ticker, p_figi, lot_qty, lot, currency, buy_price, req_type, sell_price=''):
    order_id = ''
    order_status = ''
    if g_trial_params['ENVIRONMENT'] == 'PROD':
        v_price = buy_price if req_type == 'Buy' else sell_price
        try:
            order_response = client.orders.orders_limit_order_post(figi=p_figi,
                                                                   limit_order_request={"lots": lot_qty,
                                                                                        "operation": req_type,
                                                                                        "price": v_price})
            order_id = getattr(getattr(order_response, 'payload'), 'order_id')
            order_status = getattr(order_response, 'status')
            log(order_response, g_trial+'/log.txt')
        except Exception as err: 
            output('Reqest error. ' + ticker + ' ' + req_type + ' ' + str(lot_qty) + ' lots: ' + str(err))
            log('Reqest error. ' + ticker + ' ' + req_type + ' ' +str(lot_qty) + ' lots: ' + str(err))
            return 0
    elif g_trial_params['ENVIRONMENT'] == 'TEST':
        order_status = 'Ok'
        
    if order_status == 'Ok':
        with open(g_trial + '/request.txt', 'a') as g:
                g.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S') +
                       ' ' + str(ticker).ljust(12, ' ') +
                       ' ' + str(p_figi).ljust(12, ' ') +
                       ' ' + str(lot_qty).ljust(5, ' ') +
                       ' ' + str(lot).ljust(6, ' ') +
                       ' ' + str(currency).ljust(4, ' ') +
                       ' ' + str(buy_price).ljust(10, ' ') +
                       ' ' + str(req_type).ljust(4, ' ')  +
                       ' ' + str(sell_price).ljust(10, ' ')  +  '\n')
        return lot_qty
    else:
        return 0

def get_request():
    b = []
    try:
        with open(g_trial + '/request.txt', 'r') as f:
            for item in f:
                r = {'time':datetime(int(item[0:4]), int(item[5:7]), int(item[8:10]), int(item[11:13]), int(item[14:16]), int(item[17:19])),
                          'ticker':item[20:33].rstrip(),
                          'figi':item[33:46].rstrip(),
                          'lot_qty':int(item[46:52]),
                          'lot':int(item[52:59]),
                          'currency':item[59:62],
                          'buy_price':float(item[64:75].rstrip()),
                          'type':item[75:80].rstrip()
                          }
                if item[78:].rstrip():
                    r['sell_price'] = float(item[80:].rstrip())
                b.append(r)
    except FileNotFoundError:
        return b
    return b


def check_requests():
    res = {}
    rr = get_request()
    bought = {} # Already bought
    for  i in get_bought():
        try:
            bought[i['figi']] = bought[i['figi']] + i['lot_qty']
        except KeyError:
            bought[i['figi']] = i['lot_qty']
    if g_trial_params['ENVIRONMENT'] == 'PROD':
        try:
            response = client.portfolio.portfolio_get()
            my_portfolio = {getattr(c, 'figi'):int(getattr(c, 'balance')) for c in getattr(getattr(response, 'payload'), 'positions')}
        except Exception as err:
            output('Can''t get portfolio: ' + str(err))
            log('Can''t get portfolio: ' + str(err))
            return res
        
    with open(g_trial + '/request.txt', 'w') as f:
        for r in rr:
              if (datetime.now()-r['time']).seconds > 60*60*24: # Expires after 24 hours
                  with open(g_trial + '/rejected_requests.txt', 'a') as rf:
                      try:
                          sell_price_str = ' ' + str(r['sell_price']).ljust(10, ' ')
                      except KeyError:
                          sell_price_str = ''
                      rf.write(r['time'].strftime('%Y-%m-%d %H:%M:%S') +
                         ' ' + str(r['ticker']).ljust(12, ' ') +
                         ' ' + str(r['figi']).ljust(12, ' ') +
                         ' ' + str(r['lot_qty']).ljust(5, ' ') +
                         ' ' + str(r['lot']).ljust(6, ' ') +
                         ' ' + str(r['currency']).ljust(4, ' ') +
                         ' ' + str(r['buy_price']).ljust(10, ' ') +
                         ' ' + str(r['type'].ljust(4, ' ')) + sell_price_str + '\n')
                      update_statistic(res, 'Rejected requests')
              elif r['type'] == 'Buy':
                  if g_trial_params['ENVIRONMENT'] == 'PROD':
                      try:
                         already_bougth = bought[r['figi']]
                      except KeyError:
                         already_bougth = 0
                      try:
                         buy_qty = my_portfolio[r['figi']] / r['lot'] - already_bougth
                      except KeyError:
                         buy_qty = 0

                      if buy_qty > r['lot_qty']:
                          update_statistic(res, 'Requests with error')
                          log(r['ticker'] + ' bougth more than requested: ' + str(buy_qty) + ' > ' + str(r['lot_qty']))
                  elif g_trial_params['ENVIRONMENT'] == 'TEST':
                      buy_qty = r['lot_qty']
                     
                  if buy_qty > 0:
                      with open(g_trial + '/bought.txt', 'a') as sf:
                          sf.write(r['time'].strftime('%Y-%m-%d %H:%M:%S') +
                                  ' ' + str(r['ticker']).ljust(12, ' ') +
                                  ' ' + str(r['figi']).ljust(12, ' ') +
                                  ' ' + str(buy_qty).ljust(5, ' ') +
                                  ' ' + str(r['lot']).ljust(6, ' ') +
                                  ' ' + str(r['currency']).ljust(4, ' ') +
                                  ' ' + str(r['buy_price']).ljust(10, ' ') + '\n')
                      update_statistic(res, 'Buy requests completed')
                      update_statistic(res, 'Stocks bought', buy_qty)
                      log(r['ticker'] + ' bougth: ' + str(buy_qty), g_trial+'/log.txt')
                  if r['lot_qty'] > buy_qty:
                          f.write(r['time'].strftime('%Y-%m-%d %H:%M:%S') +
                         ' ' + str(r['ticker']).ljust(12, ' ') +
                         ' ' + str(r['figi']).ljust(12, ' ') +
                         ' ' + str(r['lot_qty']-buy_qty).ljust(5, ' ') +
                         ' ' + str(r['lot']).ljust(6, ' ') +
                         ' ' + str(r['currency']).ljust(4, ' ') +
                         ' ' + str(r['buy_price']).ljust(10, ' ') +
                         ' ' + str(r['type']) + '\n')
              elif r['type'] == 'Sell':
                  if g_trial_params['ENVIRONMENT'] == 'PROD':
                      try:
                         sell_qty = r['lot_qty'] - my_portfolio[r['figi']] / r['lot']
                      except KeyError:
                         sell_qty = r['lot_qty']
                  elif g_trial_params['ENVIRONMENT'] == 'TEST':
                      sell_qty = r['lot_qty']
                  
                  
                  if sell_qty > 0:
                      sold_qty = sell(r['ticker'], sell_qty, r['sell_price'])
                      if sold_qty != sell_qty:
                          log('Error! Faild to sell necessary amount. ' + r['ticker'] + ', sold=' + str(sold_qty) + ', necessary=' + str(sell_qty))
                      update_statistic(res, 'Sell requests completed')
                      update_statistic(res, 'Stocks sold', sold_qty)
                      update_balance(sold_qty * r['lot'] * r['sell_price'] -
                                     sold_qty * r['lot'] * r['buy_price'] * float(g_trial_params['COMMISSION']) -
                                     sold_qty * r['lot'] * r['sell_price'] * float(g_trial_params['COMMISSION'])
                                     , r['currency'])
                      log(r['ticker'] + ' sold: ' + str(sold_qty), g_trial+'/log.txt')
                  if r['lot_qty'] > sell_qty:
                          f.write(r['time'].strftime('%Y-%m-%d %H:%M:%S') +
                         ' ' + str(r['ticker']).ljust(12, ' ') +
                         ' ' + str(r['figi']).ljust(12, ' ') +
                         ' ' + str(r['lot_qty']-sell_qty).ljust(5, ' ') +
                         ' ' + str(r['lot']).ljust(6, ' ') +
                         ' ' + str(r['currency']).ljust(4, ' ') +
                         ' ' + str(r['buy_price']).ljust(10, ' ') +
                         ' ' + str(r['type']).ljust(4, ' ') +
                         ' ' + str(r['sell_price']) + '\n')
    return res

def show_all_stat():
    global g_trial
    with open('trials.txt', 'r') as trials_file:
        trials = [line.strip() for line in trials_file]
    for trial in trials:
        if not trial.rstrip(): #Skip empty rows
            continue
        g_trial = trial
        output('\n' + 'Statistic:\n' + print_dict(get_statistic(), '          '))

def trade():
    global g_trial, g_params, g_trial_params, client, g_fmt, g_not_available, g_stock_price
    
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

        #Sandbox or PROD
        client = openapi.api_client(token)
        # Process trials
        for trial in trials:
            if not trial.rstrip(): #Skip empty rows
                continue
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
                output('We are not buying in the morning')
                g_not_available = []
                g_stock_price = {}
            elif g_trial_params['STOP_BUYING'] == 'Y':
                output('Buying is stopped')
            else:
                log('\n' + 'find_and_buy=\n' + print_dict(find_and_buy(), '             '))
            log('\n' + 'check_and_sell=\n' + print_dict(check_and_sell(g_trial_params['PROFIT']), '               '))
            log('\n' + 'check_requests=\n' + print_dict(check_requests(), '               '))
            log('\n' + 'Statistic:\n' + print_dict(get_statistic(), '          '))

trade()
#show_all_stat()
##g_trial_params = {}
##g_trial = 'PROD'
##g_trial_params['COMMISSION'] = 0.0005
##g_trial_params['ENVIRONMENT'] = 'PROD'
##g_fmt = '%Y-%m-%dT%H:%M:%S.%f+03:00'
##f = open('token.txt', 'r')
##token = f.read()
##f.close()
##client = openapi.api_client(token)
##check_requests()
#print(get_bought())


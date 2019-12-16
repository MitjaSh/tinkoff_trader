import datetime

# according to tariff Trader commission = 0.05%+0.05%
global commission = 0.001

def find_curve(candle_list, descent_perc = 2, advance_perc = 0.5):
    res = {}
    stage = 'Srart'
    for i in (sorted(candle_list, key=lambda x: x['time'], reverse=True)):
        if stage == 'Srart':
            res['current_value'] = i['c']
            stage = 'Advance'
        elif stage == 'Advance' and i['c'] < res['current_value'] / 100 * (100 - advance_perc):
            res['low_value'] = i['c']
            res['low_time'] = i['c']
            stage == 'Descent'
        elif stage = 'Descent' and i['c'] < res['low_value']:
            res['low_value'] = i['c']
            res['low_time'] = i['c']
        elif stage == 'Descent' and i['c'] > res['current_value'] / 100 * (100 + descent_perc):
            res['high_value'] = i['c']
            res['high_time'] = i['c']
            stage = 'Found'
        elif stage == 'Found' and i['c'] > res['high_value']:
            res['high_value'] = i['c']
            res['high_time'] = i['c']
			
	if stage == 'Found':
		return res

def log(message, file_name='log.txt'):
   f = open(file_name, 'a')
   f.write(datetime.now() + message + '\n')
   f.close()


f = open('token.txt', 'r')
token = f.read()
f.close()


#bought.txt

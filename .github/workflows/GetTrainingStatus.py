import json
import sys
data = json.loads(sys.stdin.read().replace('Training status successfully output to console', ''))
if (list(filter(lambda st: st['details']['status'] == 'InProgress' or st['details']['status'] == 'Queued', data))):
  print(2) 
else:  
  print(1)
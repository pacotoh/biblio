import json
from datetime import datetime
import logging

CONFIG_JSON = 'config/wk_config.json'
config = json.load(open(file=CONFIG_JSON, encoding='utf-8'))
wiki_path = config['path']
data_path = config['data_path']
DATE_TIME = datetime.now().strftime('%Y%m%d%H%M%S')
BATCH_SIZE = config['batch_size']

logging.basicConfig(
    filename=f'../../logs/WK{DATE_TIME}.log',
    level=logging.INFO,
    format='[%(asctime)s]: %(levelname)s %(message)s'
)


def exec():
    pass


if __name__ == '__main__':
    exec()

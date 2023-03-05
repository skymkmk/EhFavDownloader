import os

import yaml
from loguru import logger

working_dir = os.path.split(os.path.split(__file__)[0])[0]
db_dir = os.path.join(working_dir, 'data.db')


class Config:
    def __init__(self):
        self.cookies = {
            'ipb_member_id': None,
            'ipb_pass_hash': None
        }
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
                          'Chrome/108.0.0.0 Safari/537.36'
        self.proxy = {
            'enable': False
        }
        self.save_path = os.path.join(working_dir, 'doujinshi')
        self.website = 'e-hentai.org'
        self.connect_limit = 3
        try:
            with open(os.path.join(working_dir, 'config.yaml'), encoding='UTF-8') as f:
                config: dict = yaml.safe_load(f)
                if 'cookies' not in config:
                    logger.error('Cookies not found.')
                    exit(2)
                elif not all(i in config['cookies'] for i in ['ipb_member_id', 'ipb_pass_hash']):
                    logger.error('ipb_member_id or ipb_pass_hash not found.')
                    exit(2)
                self.cookies['ipb_member_id'] = config['cookies']['ipb_member_id']
                self.cookies['ipb_pass_hash'] = config['cookies']['ipb_pass_hash']
                if 'website' in config:
                    if config['website'] in ['e-hentai.org', 'exhentai.org']:
                        self.website = config['website']
                    else:
                        logger.warning('The website in config.yaml is not correct. Use e-hentai.org as default.')
                if self.website == 'exhentai.org':
                    if 'igneous' in config['cookies']:
                        self.cookies['igneous'] = config['cookies']['igneous']
                    else:
                        logger.error('Because you have configured the website as exhentai.org, we need the igneous '
                                     'value. This value is not found in your configuration file.')
                        exit(3)
                if 'User-Agent' in config:
                    self.user_agent = config['User-Agent']
                if 'proxy' in config:
                    if 'enable' in config['proxy']:
                        if config['proxy']['enable'] is True:
                            if 'url' in config['proxy']:
                                self.proxy['enable'] = True
                                self.proxy['url'] = config['proxy']['url']
                            else:
                                logger.warning('Not detected proxy url. The proxy will still be disabled.')
                if 'save_path' in config:
                    self.save_path = config['save_path']
                if 'connect_limit' in config:
                    self.connect_limit = config['connect_limit']
        except FileNotFoundError:
            logger.error("Can't find config file.")
            exit(1)

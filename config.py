import os

import yaml
from loguru import logger

import exitcodes

WORKING_DIR = os.path.split(__file__)[0]
DB_DIR = os.path.join(WORKING_DIR, 'data.db')
cookies = {
    'ipb_member_id': None,
    'ipb_pass_hash': None,
}
save_path = os.path.join(WORKING_DIR, 'doujinshi')
website = 'e-hentai.org'
connect_limit = 3
enable_tag_translation = False
retry_time = 3
save_as_cbz = False
metadata_full_update = False
try:
    with open(os.path.join(WORKING_DIR, 'config.yaml'), encoding='UTF-8') as f:
        config: dict = yaml.safe_load(f)
        if 'cookies' not in config:
            logger.error('Cookies not found.')
            exit(exitcodes.NO_VALID_COOKIE_DETECTED)
        elif not all(i in config['cookies'] for i in ['ipb_member_id', 'ipb_pass_hash']):
            logger.error('ipb_member_id or ipb_pass_hash not found.')
            exit(exitcodes.NO_VALID_COOKIE_DETECTED)
        cookies['ipb_member_id'] = config['cookies']['ipb_member_id']
        cookies['ipb_pass_hash'] = config['cookies']['ipb_pass_hash']
        if 'website' in config:
            if config['website'] in ['e-hentai.org', 'exhentai.org']:
                website = config['website']
            else:
                logger.warning('The website in config.yaml is not correct. Use e-hentai.org as default.')
        if website == 'exhentai.org':
            if 'igneous' in config['cookies']:
                cookies['igneous'] = config['cookies']['igneous']
            else:
                logger.error('Because you have configured the website as exhentai.org, we need the igneous '
                             'value. This value is not found in your configuration file.')
                exit(exitcodes.NO_VALID_COOKIE_DETECTED)
        if 'save_path' in config:
            save_path = config['save_path']
        if 'connect_limit' in config:
            connect_limit = config['connect_limit']
        if 'enable_tag_translation' in config:
            enable_tag_translation = config['enable_tag_translation']
        if 'retry_time' in config:
            retry_time = config['retry_time']
        if 'save_as_cbz' in config:
            save_as_cbz = config['save_as_cbz']
except FileNotFoundError:
    logger.error("Can't find config file.")
    exit(exitcodes.CONFIG_FILE_NOT_FOUND)

# EhFavDownloader

[简体中文](README.md)

A script for backing up the E-Hentai favourites. Generating CBZ files compatible with Komga for easy uploading of downloaded items to Komga.

## Note for English version

This copy was translated from the Chinese version by DeepL and ChatGPT. If there is any discrepancy with the Chinese version, the Chinese version shall prevail.

## Tips

If there is something you don't know (e.g. how to get cookies), please consult search engines like Google, Bing or artificial intelligence like ChatGPT first.

These products bring together the best of human intelligence, and it's much more efficient to ask them than asking around for help.

## Disclaimer

This script is for personal use, and is hosted on GitHub for your convenience only. Due to my limited skills, the code is bound to contain a lot of problems. You should have some hands-on experience with this script before using it.

You should be aware that this script is not responsible for any potential damages, including but not limited to IP blocking, account banning, file loss, etc. Please read the [license](LICENSE) used for this project for details.

## Download tips for the e-hentai.org site

Due to the recent deployment of the CloudFlare shield on e-hentai.org, this script does not use a headless browser to execute JS scripts and cannot be bypassed at this time. Since the CloudFlare shield has a higher probability of triggering, downloading from e-hentai.org is likely to trigger a 403 denial of access. The temporary solution is to use the exhentai.org site for downloading, so please use e-hentai.org for downloading at your own discretion.

## Upgrade Notice

Version 0.2 has made changes to certain configuration options in the configuration file. If you are upgrading from an older version, please take note of the modifications required in the configuration file.

## How to use

- Install a copy of [Python](https://www.python.org). The minimum version required is 3.7, but this script is written in 3.11, so we recommend using 3.11.
- Install the dependencies needed for this project. In general, you only need to execute
  ```shell
  pip install -r requirements.txt
  ```
  and you're good to go.
- Make a copy of config.yaml.example, rename it to config.yaml, and then make changes to the configuration according to the comments in the file. Note the YAML syntax, if you are not sure you can ask a search engine.
- Just run the script or add it to a relevant scheduled task (e.g. Windows Task Scheduler, Linux Crontab, etc.).
# Disney+ Account Checker
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Multi-threaded](https://img.shields.io/badge/Multi--Threaded-Yes-success.svg)
![Disney Account Checker ](https://cdn.discordapp.com/attachments/1413501158625906811/1419409520446275674/image.png?ex=68d1a7a1&is=68d05621&hm=2488d99df9a9d1282ca22dcc667ce8b1ad65b6822b30168a91fbafc9b52f625e&)

## Features

- Multi-threaded
- Proxy support (rotating residential proxies)
- Discord webhook notifications
- Real-time status updates with colored output
- Configurable settings via config file

## Usage

1. Install requirements: `pip install requests colorama`
2. Configure `settings.cfg` with your proxies and settings
3. Add combo to `accounts.txt` in email:password format
4. Run: `python main.py`

## Configuration

Edit `settings.cfg` to enable/disable features:
- Proxy usage and file path
- Thread count
- Discord webhook notifications

## Disclaimer

This tool is for educational purposes only.

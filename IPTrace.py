import requests
import folium
import re
import logging
from pyfiglet import Figlet
from colorama import init, Fore

init(autoreset=True)

IP_API_URL = 'http://ip-api.com/json/{ip}'
VPN_PROXY_CHECK_URL = 'https://ipinfo.io/{ip}/json'

logging.basicConfig(filename='ip_info.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class IPInfoFetcher:
    PRIVATE_IP_RANGES = [
        re.compile(r"^10\..*"),
        re.compile(r"^172\.(1[6-9]|2[0-9]|3[01])\..*"),
        re.compile(r"^192\.168\..*")
    ]

    @staticmethod
    def validate_ip(ip):
        ipv4_pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
        ipv6_pattern = re.compile(r"^([0-9a-fA-F]{1,4}:){7}([0-9a-fA-F]{1,4}|:)$")
        return ipv4_pattern.match(ip) or ipv6_pattern.match(ip)

    @classmethod
    def is_private_ip(cls, ip):
        return any(pattern.match(ip) for pattern in cls.PRIVATE_IP_RANGES)

    @staticmethod
    def get_ip_info(ip):
        try:
            response = requests.get(IP_API_URL.format(ip=ip)).json()
            if response.get('status') == 'fail':
                logging.error(f"IP API error: {response.get('message')}")
                return None
            return response
        except requests.exceptions.RequestException as e:
            logging.error(f'Connection error while fetching IP info: {str(e)}')
            return None

    @staticmethod
    def check_vpn_or_proxy(ip):
        try:
            response = requests.get(VPN_PROXY_CHECK_URL.format(ip=ip)).json()
            privacy = response.get('privacy', {})
            if privacy.get('proxy', False) or privacy.get('vpn', False):
                return "Используется VPN/Прокси"
            return "Нет"
        except requests.exceptions.RequestException as e:
            logging.error(f"Ошибка при проверке VPN/Прокси: {str(e)}")
            return "Не удалось определить"

    def get_info(self, ip):
        if not self.validate_ip(ip):
            print(Fore.RED + '[!] Неправильный IP-адрес. Попробуйте снова.')
            return None

        if self.is_private_ip(ip):
            print(Fore.YELLOW + '[!] Введенный IP-адрес является локальным (частным).')
            return None

        ip_info = self.get_ip_info(ip)
        if not ip_info:
            print(Fore.RED + '[!] Не удалось получить информацию по IP-адресу.')
            return None

        vpn_check = self.check_vpn_or_proxy(ip)
        ip_info['VPN/Прокси'] = vpn_check

        return ip_info

class IPMapVisualizer:
    @staticmethod
    def visualize_on_map(ip_info):
        if 'lat' in ip_info and 'lon' in ip_info:
            area = folium.Map(location=[ip_info.get('lat'), ip_info.get('lon')], zoom_start=10)
            folium.Marker(
                location=[ip_info.get('lat'), ip_info.get('lon')],
                popup=f"{ip_info.get('city')}, {ip_info.get('regionName')} ({ip_info.get('country')})",
                tooltip="Кликните для подробностей"
            ).add_to(area)
            folium.Circle(
                location=[ip_info.get('lat'), ip_info.get('lon')],
                radius=5000,
                color='blue',
                fill=True,
                fill_opacity=0.1
            ).add_to(area)
            map_filename = f'{ip_info.get("query")}_{ip_info.get("city")}.html'
            area.save(map_filename)
            print(Fore.YELLOW + f'[+] Карта сохранена как {map_filename}')
        else:
            print(Fore.RED + '[!] Не удалось визуализировать местоположение на карте')

def main():
    preview_text = Figlet(font='slant')
    print(Fore.MAGENTA + preview_text.renderText('Termux_Laif'))

    ip = input(Fore.CYAN + 'Пожалуйста, введите целевой IP: ')

    fetcher = IPInfoFetcher()
    ip_info = fetcher.get_info(ip)

    if ip_info:
        for k, v in ip_info.items():
            print(Fore.GREEN + f'{k} : {v}')
        
        visualizer = IPMapVisualizer()
        visualizer.visualize_on_map(ip_info)

if __name__ == '__main__':
    main()

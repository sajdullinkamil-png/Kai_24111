import csv
import time
import random
import requests
from bs4 import BeautifulSoup
class IXBTParser:
    def __init__(self):
        self.base_url = "https://ixbt.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Referer': 'https://google.com',
            'Connection': 'keep-alive'
        }
        self.scraped_data = []
    def fetch_page(self, url):
        """Безопасно загружает HTML-код страницы, используя сессию."""
        try:
            session = requests.Session()
            response = session.get(url, headers=self.headers, timeout=15)
            print(f"-> Код ответа сервера: {response.status_code}")
            if response.status_code == 200:
                response.encoding = 'utf-8'
                if "Доступ ограничен" in response.text or "Cloudflare" in response.text:
                    print("![БЛОК] Сайт выдал страницу защиты от роботов.")
                    return None
                return response.text
            return None
        except requests.RequestException as e:
            print(f"![ОШИБКА] Ошибка сети при запросе к {url}: {e}")
            return None
    def clean_text(self, text):
        """Очищает текст от лишних пробелов, переносов и мусора."""
        if not text:
            return ""
        return " ".join(text.strip().split())
    def parse_page(self, html):
        """Универсальный сборщик новостей для iXBT по структуре заголовков."""
        if not html:
            return False
        soup = BeautifulSoup(html, 'html.parser')
        parsed_count = 0
        elements = soup.find_all(['h2', 'h1', 'li', 'div'])
        for el in elements:
            # Находим тег ссылки
            a_tag = el if el.name == 'a' else el.find('a')
            if not a_tag:
                continue
            title = self.clean_text(a_tag.get_text())
            link = a_tag.get('href', '')
            if len(title) < 20 or not link:
                continue
            if any(x in link for x in ['/tags/', '/forum/', '/live/', '/user/', '/merch/', 'javascript:']):
                continue
            if not any(x in link for x in ['/news/', '/articles/', '/games/', '/live/', '/brand/']):
                continue
            if link and not link.startswith('http'):
                link = self.base_url.rstrip('/') + '/' + link.lstrip('/')
            date_str = "В ленте"
            parent = el.parent if el.name == 'a' else el
            time_tag = parent.find(['span', 'em', 'div'])
            if time_tag:
                time_text = self.clean_text(time_tag.get_text())
                if time_text and any(char.isdigit() for char in time_text) and len(time_text) < 15:
                    date_str = time_text
            if not any(d['link'] == link for d in self.scraped_data):
                self.scraped_data.append({
                    'title': title,
                    'link': link,
                    'date': date_str
                })
                parsed_count += 1
        print(f"-> Успешно извлечено новостей со страницы: {parsed_count}")
        return parsed_count > 0
    def run(self, max_pages=2):
        """Запускает обход страниц пагинации ленты новостей."""
        print("Старт парсинга iXBT.com...")
        for page in range(1, max_pages + 1):
            print(f"\n--- Парсим страницу {page} из {max_pages} ---")
            if page == 1:
                url = f"{self.base_url}/news/"
            else:
                url = f"{self.base_url}/news/?page={page}"
            print(f"Запрос к URL: {url}")
            html = self.fetch_page(url)
            success = self.parse_page(html)
            if not success:
                print("Данные не найдены на этой странице. Прерываем обход.")
                break
            delay = random.uniform(2.5, 4.5)
            print(f"Ожидание перед следующей страницей: {delay:.2f} сек...")
            time.sleep(delay)
    def save_to_csv(self, filename='ixbt_news.csv'):
        if not self.scraped_data:
            print("\n![ОТМЕНА] Нет данных для сохранения. Файл не создан.")
            return
        with open(filename, mode='w', encoding='utf-8-sig', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['title', 'link', 'date'])
            writer.writeheader()
            writer.writerows(self.scraped_data)
        print(f"\n[УСПЕХ] Создан файл {filename}. Всего уникальных записей: {len(self.scraped_data)}")
if __name__ == '__main__':
    parser = IXBTParser()
    parser.run(max_pages=2)
    parser.save_to_csv('ixbt_portfolio_news.csv')

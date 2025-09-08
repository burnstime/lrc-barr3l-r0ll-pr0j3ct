import os
import requests
from bs4 import BeautifulSoup

def main():
    target = os.environ.get('TARGET')
    if not target:
        print('TARGET environment variable not set.')
        return
    url = f'{target}/login'
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string if soup.title else 'No title found'
        print(f'Page title: {title}')
    except Exception as e:
        print(f'Error fetching {url}: {e}')

if __name__ == '__main__':
    main()

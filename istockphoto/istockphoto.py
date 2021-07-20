import requests
import os
from bs4 import BeautifulSoup
from time import sleep

os.system('chcp 65001')

# Сайт к которому выполняется парсер
site = 'https://www.istockphoto.com'

# Поисковый запрос
search = ''
# Параметры авторизации
username = ''
password = ''
# Путь к папке с изображениями
download = ''
# Путь к файлу номера последней обработанной страницы
path_page = download + ''
# Путь к файлу описаний к изображениям
path_tsv = download + ''

# Адресная строка для страницы авторизации
url = site + '/sign-in'
# Создание сессии и авторизация
session = requests.session()
loging = session.post(url, {
    'new_session[username]': username,
    'new_session[password]': password
})


# Присваивание номера первой страницы поискового запроса
if os.path.exists(path_page):
    file_page = open(path_page, 'r')
    last_page = file_page.read()
    last_page = int(last_page)
    file_page.close()
else:
    last_page = 1

# Адресная строка для поискового запроса
url = site + '/en/search/2/image/'
parameters = {'phrase': search, 'page': last_page, 'mediatype': 'photography'}
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/75.0.3770.142 Safari/537.36'
}
# Получение страницы в формате Fixed
response = session.get(url, params=parameters, headers=headers, cookies={
    'sp=sf=&ci': 't%25252Crf&gsrp=0&sgl=fixed'
})
# Преобразование страницы в lxml
soup = BeautifulSoup(response.text, 'lxml')

# Время ожидания после проверки на капчу
time_to_sleep_when_captcha = 5
# Флаг первой итерации
is_not_first = False
# Присвоение номера последенй страницы поискового запроса
last_page_num = soup.find('span', class_='PaginationRow-module__lastPage___1gtme').text
last_page_num = int(last_page_num)

# Цикл по обработке страниц
while parameters['page'] <= last_page_num:
    # Обработка первой итерации
    if is_not_first:
        response = session.get(url, params=parameters)
        soup = BeautifulSoup(response.text, 'lxml')
    else:
        is_not_first = True
    # Проверка на ошибки в сессии
    if response.status_code == 500:
        continue
    if response.status_code == 404:
        break
    # Открытие файла для выгрузки описаний
    tsv_file = open(path_tsv, 'a', encoding='utf-8')
    # Цикл для парсинга страницы
    for parse in soup.find_all('div', class_='FixedAsset-module__galleryFixedAsset___2QSXC'):
        # Поимка ошибки по капче
        try:
            # Получение id изображения
            img_id = parse['data-asset-id']
            path = download + '/' + img_id + '.jpg'
            # Проверка на дубликаты
            if not os.path.exists(path):
                # Получение описания
                title = parse.find('div', class_="FixedAssetContent-module__title___2W6Re", title=True)
                title = title['title'].replace('\n', ' ')
                # Получение изображения
                img = parse.find('img', src=True)
                src = img['src']
                img_data = session.get(src).content
                # Выгрузка изображения и описания к нему
                img_file = open(path, 'wb+')
                img_file.write(img_data)
                tsv_file.write(download + img_id + '.jpg' + '\t' + title + '\t' + src + '\n')
                img_file.close()
        except:
            # Ждём, пока капча не отпустит
            sleep(time_to_sleep_when_captcha)
            time_to_sleep_when_captcha += 1
            print('error')
    time_to_sleep_when_captcha = 5
    tsv_file.close()
    # Запоминаем номер обработанной страницы
    now_page = open(path_page, 'w')
    now_page.write(str(parameters['page']))
    # Изменение параметра "страница" в адресной строке
    parameters['page'] += 1

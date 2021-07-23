import logging
import requests
# from requests.adapters import HTTPAdapter
# from requests.packages.urllib3.util.retry import Retry
import os
import sys
from bs4 import BeautifulSoup
from time import sleep
from fake_useragent import UserAgent


def requests_retry_session(
    retries=3,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504),
    session=None,
):
    """
    Build a retry session for requests
    """
    session = session or requests.Session()
    retry = requests.packages.urllib3.util.retry.Retry(
        total=retries,
        read=retries,
        connect=retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session



logging_filename = f"{sys.argv[0]}_{sys.argv[1].replace(' ','_')}.log" if len(sys.argv) > 1 else f"{sys.argv[0]}.log"
file_handler = logging.FileHandler(logging_filename)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
logging.basicConfig(
    level=logging.DEBUG,
    datefmt="%Y-%m-%d %H:%M:%S",
    format="%(asctime)s %(name)s - %(levelname)s - %(message)s",
    handlers=[console_handler, file_handler]
)

# os.system('chcp 65001')

headers = {
    'User-Agent': UserAgent().random
}

# Сайт к которому выполняется парсер
site = 'https://www.istockphoto.com'

# Поисковый запрос
# search = ''
search = sys.argv[1] if len(sys.argv) > 1 else ''
# Параметры авторизации
username = 'markpolyak@smedx.com'
password = 'asdf1234'
# Путь к папке с изображениями
download = sys.argv[2] if len(sys.argv) > 2 else 'images'
# Путь к файлу описаний к изображениям
path_tsv = sys.argv[3] if len(sys.argv) > 3 else 'labels.tsv'
# Путь к файлу номера последней обработанной страницы
path_page = sys.argv[4] if len(sys.argv) > 4 else 'loaded_pages.txt'
# start from last page
start_from_last_page = (sys.argv[5]=='1') if len(sys.argv) > 5 else False

logging.info("Search query: %s. Download folder: %s. Captions file: %s. Loaded pages counter: %s. Start from last page: %s", search, download, path_tsv, path_page, start_from_last_page)

# new session object
# session = requests.session()
session = requests_retry_session()
session.headers.update(headers)
logging.info("User-Agent: %s", session.headers['User-Agent'])

# authorization url
url = site + '/sign-in'
# authorize session
response = session.post(url, {
    'new_session[username]': username,
    'new_session[password]': password
})
if response.status_code != 200:
    logging.critical("Unable to initialize session. Response code %d. Response headers %s. Response text %s", response.status_code, response.headers, response.text)
    sys.exit(1)


# Присваивание номера первой страницы поискового запроса
if os.path.exists(path_page):
    file_page = open(path_page, 'r')
    last_page = file_page.read()
    last_page = int(last_page)
    file_page.close()
else:
    last_page = 1

# Адресная строка для поискового запроса
url = site + '/en/search/2/image'
parameters = {'phrase': search.strip(), 'page': last_page, 'mediatype': 'photography', 'sort': 'newest'}
if len(search) < 1:
    del parameters['phrase']
# Получение страницы в формате Fixed
response = session.get(url, params=parameters,
    cookies={'sp=sf=&ci': 't%25252Crf&gsrp=0&sgl=fixed'}
)
if response.status_code != 200:
    logging.critical("Unable to load page. Response code %d. Response headers %s. Response text %s", response.status_code, response.headers, response.text)
    sys.exit(1)
# Преобразование страницы в lxml
soup = BeautifulSoup(response.text, 'lxml')

# Время ожидания после проверки на капчу
time_to_sleep_when_captcha = 5
# Флаг первой итерации
is_not_first = False
# Присвоение номера последенй страницы поискового запроса
last_page_num = soup.find('span', class_='PaginationRow-module__lastPage___1gtme').text
last_page_num = int(last_page_num)
logging.info("Total %d pages are available for download", last_page_num)
if start_from_last_page:
    parameters['page'] = last_page_num - last_page

repeat_on_error_counter = 0

# Цикл по обработке страниц
while (not start_from_last_page and parameters['page'] <= last_page_num) or (start_from_last_page and parameters['page'] > 0):
    logging.info("Parsing page %d out of %d ...", parameters['page'], last_page_num)
    # Обработка первой итерации
    if is_not_first:
        response = session.get(url, params=parameters, cookies={'sp=sf=&ci': 't%25252Crf&gsrp=0&sgl=fixed'})
        soup = BeautifulSoup(response.text, 'lxml')
    else:
        is_not_first = True
    # Проверка на ошибки в сессии
    if response.status_code == 500:
        logging.error("Response code %d for url %s with params %s", response.status_code, url, parameters)
        continue
    if response.status_code == 404:
        logging.critical("Response code %d for url %s with params %s", response.status_code, url, parameters)
        break
    if response.status_code == 301:
        logging.warning("Response code %d for url %s with params %s", response.status_code, url, parameters)
    # Открытие файла для выгрузки описаний
    tsv_file = open(path_tsv, 'a', encoding='utf-8')
    # Цикл для парсинга страницы
    image_elements = soup.find_all('div', class_='FixedAsset-module__galleryFixedAsset___2QSXC')
    if len(image_elements) < 1:
        logging.error("Unable to parse page %d. No images were found", parameters['page'])
        # Ждём, пока блокировка не отключится
        sleep(time_to_sleep_when_captcha)
        time_to_sleep_when_captcha += 1
        repeat_on_error_counter += 1
        if repeat_on_error_counter > 100:
            logging.critical("Too many page download attempts have failed")
            sys.exit(1)
        else:
            continue
    else:
        repeat_on_error_counter = 0
    new_image_count = 0
    dup_image_count = 0
    err_count = 0
    for element in image_elements:
        image_id = -1
        # Поимка ошибки по капче
        try:
            # Получение id изображения
            img_id = element['data-asset-id']
            path = download + '/' + img_id + '.jpg'
            # Проверка на дубликаты
            if not os.path.exists(path):
                # Получение описания
                title = element.find('div', class_="FixedAssetContent-module__title___2W6Re", title=True)
                if not title:
                    logging.error("Title not found for image %s on page %d. Page contents: %s", img_id, parameters['page'], element)
                title = title['title'].replace('\n', ' ')
                # Получение изображения
                img = element.find('img', src=True)
                src = img['src']
                img_data = session.get(src).content
                # Выгрузка изображения и описания к нему
                img_file = open(path, 'wb+')
                img_file.write(img_data)
                tsv_file.write(path + '\t' + title + '\t' + src + '\n')
                img_file.close()
                new_image_count += 1
            else:
                dup_image_count += 1
                logging.warning("File %s already exists", path)
        except Exception:
            logging.exception("Unable to parse page %d, download image %s or save it to disk", parameters['page'], image_id)
            # Ждём, пока капча не отпустит
            sleep(time_to_sleep_when_captcha)
            time_to_sleep_when_captcha += 1
            err_count += 1
            # print('error')
    logging.info("Page had %d elements. %d images were saved. %d images were downloaded earlier. %d images caused a parser error.", len(image_elements), new_image_count, dup_image_count, err_count)
    time_to_sleep_when_captcha = 5
    tsv_file.close()
    # Запоминаем номер обработанной страницы
    now_page = open(path_page, 'w')
    now_page.write(str(parameters['page']))
    # Изменение параметра "страница" в адресной строке
    if start_from_last_page:
        parameters['page'] -= 1
    else:
        parameters['page'] += 1

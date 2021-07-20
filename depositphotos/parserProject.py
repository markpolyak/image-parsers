import requests
from bs4 import BeautifulSoup
import os
import sys


# Функция скачивания фотографий из одной категории
def downloading(category):
    global count_of_photos
    # Смещение относительно первой фотографии в категории, которое будет установлено в ссылку для следующего шага цикла
    # (всегда кратно 100)
    offset = 100
    # Сслыка на текущую обрабатываемую страницу
    url_offset = ''
    if offset == 100:
        url_offset += category
    else:
        url_offset += category.replace('?', '?offset=' + str(offset - 100) + '&')

    # Цикл по страницам категории (крайнее значение равно требуемому количеству фотографий из одной категории)
    # (всегда кратно 100)
    while offset <= 100000:
        # Теги section
        photo_section = ''
        # Флаг наличия тегов section
        section_found = False
        # Получение тегов секций
        while not section_found:
            try:
                response_url = requests.get(url_offset)
                soup_url = BeautifulSoup(response_url.text, 'lxml')
                photos_info = soup_url.find('div', class_='flex-files flex-files_xwide flex-files_like-grid _slider')

                photo_section = photos_info.find_all('section')
                section_found = True
            except AttributeError:
                print('An error was handled!')

        # Вытаскивание ссылок и описаний фотографий
        link_and_description_photos = []
        for n_photo_section, item_photo_section in enumerate(photo_section):
            link_and_description_photos.append(item_photo_section.find('img'))

        # Запись ссылок и описаний фотографий в отдельные массивы
        link_photos = []
        description_photos = []
        for n_l_and_d_photos, item_l_and_d_photos in enumerate(link_and_description_photos):
            link_photos.append(item_l_and_d_photos.attrs.get('src', '').replace('/950/', '/600/'))
            description_photos.append(item_l_and_d_photos.attrs.get('alt', ''))
            if link_photos[n_l_and_d_photos] == '':
                link_photos[n_l_and_d_photos] = item_l_and_d_photos.attrs.get('data-src', '').replace('/950/', '/600/')

        # Скачивание фотографий и запись текстового описания в файл
        for n_link_photos, item_link_photos in enumerate(link_photos):
            photo = requests.get(item_link_photos)
            out_photo = open('photos\\' + str(count_of_photos) + '.jpg', 'wb')
            out_photo.write(photo.content)
            out_photo.close()
            out_description_photo = open('descriptionPhotos.tsv', 'a', encoding='utf-8')
            out_description_photo.write(str(count_of_photos) + '.jpg\t' + description_photos[n_link_photos] + '\n')
            out_description_photo.close()
            count_of_photos += 1

        # Установка сслыки на следующую обрабатываемую страницу
        url_offset = item_categories.replace('?', '?offset=' + str(offset) + '&')
        # Установка смещения
        offset += 100


# Проверка наличия папки для фото
if not os.path.exists('photos'):
    os.mkdir('photos')

# Основная ссылка
url = 'https://depositphotos.com/search-new/index.html'

# Запрос к сайту
response_index = requests.get(url)
# Проверка работоспособности сайта
if response_index.status_code == 404:
    print('The site is not working. Try again later.')
    sys.exit(1)
if response_index.status_code == 500:
    print('The site is not working. Try again later.')
    sys.exit(1)

# Записываем xml в переменную
soup_index = BeautifulSoup(response_index.text, 'lxml')

# Поиск тега, в котором хранится информация о категориях
categories = soup_index.find('nav', class_='search-related')

# Поиск тега, в котором хранятся ссылки на категории
info_link_categories = categories.find_all('a', class_='search-related__link _related-link')

# Вытаскивание ссылок на категории
link_categories = []
for n_info_categories, item_info_categories in enumerate(info_link_categories):
    link_categories.append('https://depositphotos.com' + item_info_categories['href'])

# Преобразование ссылок на категории
for n_link_categories, item_link_categories in enumerate(link_categories):
    i = item_link_categories.find('&search_params')
    result_link = ''
    for counter in range(0, i):
        result_link += item_link_categories[counter]
    link_categories[n_link_categories] = result_link

# Количество фотографий в файле используемое в качестве названия фотографий (меняется при каждом запуске программы)
count_of_photos = 0
# Категория с которой начинается скачивание (значение от 0 до 9)
start_category = 0
# Флаг скачивания категорий (True - докачка категории, False - скачивание категорий от стартовой до последней)
downloading_one_category = False

# Цикл для прохода по категориям
for n_categories, item_categories in enumerate(link_categories):
    # Если докачивается только одна категория, то функция скачивания вызывается только для нее
    if downloading_one_category and (n_categories == start_category):
        downloading(item_categories)
    # В противном случае скачиваются категории от стартовой до последней
    elif (not downloading_one_category) and (n_categories >= start_category):
        downloading(item_categories)

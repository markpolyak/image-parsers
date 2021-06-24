# scraper.py
import os

import requests
from bs4 import BeautifulSoup

f = open('foto_discript.tsv', 'r')  # берёт уже загруженные данные из файла
data = f.read().split('\n')
lenData = len(data)
f.close()

url = 'https://lightfieldstudios.net/search-new/' # ссылка на сайт
pages = 1  # задаёт начальную страничку парсинга
isFirst = 1  # не трогать
u = 0  # не трогать
countImg = 0  # количество скаченных изображений

if not os.path.exists('upload'):  # создаём папку для загрузки картинок
    os.mkdir('upload')

while pages < 4: # менять в зависимости от хотелки
    # 1. pages < 4 - ограничить парсинг по страницам;
    # 1. countImg < 200000 - ограничить парсинг по изображениям;
    response = requests.get(url+"page"+str(pages))  # запрос к сайту
    while response.status_code == 500:  # исли запрос не удачный, пробуем ещё
        response = requests.get(url + "page" + str(pages))

    if response.status_code == 404:  # если сайту кирдык, коректный выход из программы
        break
    soup = BeautifulSoup(response.text, 'lxml')  # записываем xml в переменную

    for img in soup.find_all('img', src=True):  # проходим по всем значениям, которые удовлетворяют условию
        if lenData == 1 or lenData == 0:  # если до этого не было парсинга
            f = open('foto_discript.tsv', 'a')  # открываем сайт для записи в конец
            imgName = img['src'].split('/')[-1]  # и берём только последнюю часть

            if isFirst == 1:
                # записываем в файлик данные
                f.write('upload/' + imgName[36:] + '\t' + img['alt'].split('—')[0][:-1] + '\t' + img['src'])
                lenData == u
                isFirst = 0
            else:
                # записываем в файлик данные
                f.write('\n' + 'upload/' + imgName[36:] + '\t' + img['alt'].split('—')[0][:-1] + '\t' + img['src'])

            imgData = requests.get(img['src']).content  # берём изображение

            fImg = open('upload' + '/' + imgName[36:], 'wb')  # загружаем изображение в файл
            fImg.write(imgData)
            fImg.close()
            f.close()
        else:
            # переменные с описанием и изображением
            discript = img['alt'].split('—')[0][:-1]
            imgName = img['src'].split('/')[-1]
            # если картинка с сайта не совпадает с первой в дате
            if imgName[36:-4] != data[0].split('\t')[0][7:-4] and u < lenData:
                # то по стандарту грузим их в файлик
                if isFirst == 1:
                    f = open('foto_discript.tsv', 'w')
                    isFirst = 0
                else:
                    f = open('foto_discript.tsv', 'a')
                f.write('upload/' + imgName[36:] + '\t' + discript + '\t' + img['src'] + '\n')

                imgData = requests.get(img['src']).content

                fImg = open('upload' + '/' + imgName[36:], 'wb')
                fImg.write(imgData)
                fImg.close()
                f.close()

            else:
                # если мы нашли, откуда начинали, подгружаем весю дату
                if u < lenData:
                    if isFirst == 1:
                        f = open('foto_discript.tsv', 'w')
                        isFirst = 0
                        pages = 0
                    else:
                        f = open('foto_discript.tsv', 'a')
                        pages -= 1
                    for item in data:
                        if (lenData - 1) == u:
                            f.write(item)
                        else:
                            f.write(item + '\n')
                        u += 1
                    f.close()
                    countImg += u
                    pages += int(u/60)
            if u > lenData:
                # после подгрузки даты, по стандарту качаем из сайта данные
                f = open('foto_discript.tsv', 'a')

                f.write('\n' + 'upload/' + imgName[36:] + '\t' + discript + '\t' + img['src'])

                imgData = requests.get(img['src']).content

                fImg = open('upload' + '/' + imgName[36:], 'wb')
                fImg.write(imgData)
                fImg.close()
                f.close()

            if u == lenData:
                u += 1
                break

        countImg += 1
    pages += 1

# удаление \n с конца файла
f = open('foto_discript.tsv', 'r')
temp = f.readlines()
f.close()
if temp[len(temp)-1][-1] == '\n':
    temp[len(temp)-1] = temp[len(temp)-1][:-1]
    f = open('foto_discript.tsv', 'w')
    for i in temp:
        f.write(i)
    f.close()

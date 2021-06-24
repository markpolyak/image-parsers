# scraper.py
import os

import requests
from bs4 import BeautifulSoup

f = open('foto_discript.tsv', 'r')
data = f.read().split('\n')
lenData = len(data)
f.close()

url = 'https://lightfieldstudios.net/search-new/'
pages = 1 # задаёт начальную страничку парсинга
isFirst = 1
u = 0
countImg = 0 # количество скаченных изображений

if not os.path.exists('upload'):
    os.mkdir('upload')

while pages < 4: # менять в зависимости от хотелки
    # 1. pages < 4 - ограничить парсинг по страницам;
    # 1. countImg < 200000 - ограничить парсинг по изображениям;
    response = requests.get(url+"page"+str(pages))
    while response.status_code == 500:
        response = requests.get(url + "page" + str(pages))
    if response.status_code == 404:
        break
    soup = BeautifulSoup(response.text, 'lxml')

    for img in soup.find_all('img', src=True):
        if lenData == 1 or lenData == 0:
            f = open('foto_discript.tsv', 'a')
            imgName = img['src'].split('/')[-1]

            if isFirst == 1:
                f.write('upload/' + imgName[36:] + '\t' + img['alt'].split('—')[0][:-1] + '\t' + img['src'])
                lenData == u
                isFirst = 0
            else:
                f.write('\n' + 'upload/' + imgName[36:] + '\t' + img['alt'].split('—')[0][:-1] + '\t' + img['src'])
            imgData = requests.get(img['src']).content

            fImg = open('upload' + '/' + imgName[36:], 'wb')
            fImg.write(imgData)
            fImg.close()
            f.close()
        else:
            discript = img['alt'].split('—')[0][:-1]
            imgName = img['src'].split('/')[-1]
            if imgName[36:-4] != data[0].split('\t')[0][7:-4] and u < lenData:
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
    print(countImg)

f = open('foto_discript.tsv', 'r')
temp = f.readlines()
f.close()
if temp[len(temp)-1][-1] == '\n':
    temp[len(temp)-1] = temp[len(temp)-1][:-1]
    f = open('foto_discript.tsv', 'w')
    for i in temp:
        f.write(i)
    f.close()

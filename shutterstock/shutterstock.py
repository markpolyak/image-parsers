import urllib3
import requests
from bs4 import BeautifulSoup
import re
import csv
from PIL import Image
import os

class ShutterstockParser:

    userAgent = {'user-agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) ..'}
    pageCount = 0
    loadedPageCount = 0
    imageFolderPath = ""

    def __init__(self, imageFolderPath):
        self.imageFolderPath = imageFolderPath

    def parseAllPages(self):
        loadedPageCount = self.__readLoadedPageCount()
        pageCount = self.__getInitPageCount()
        while pageCount > loadedPageCount:
            self.parsePage(pageCount - loadedPageCount)
            loadedPageCount += 1
            self.__saveLoadedPageCount(loadedPageCount)

    def parsePage(self, pageId = 1):
        pageData = self.__loadPage(pageId)
        if pageData is not None:
            soup = BeautifulSoup(pageData, 'html.parser')

            imageTables = soup.find_all('div', {'class': 'z_h_b900b'})
            for imageDiv in imageTables:
                imageInfo = imageDiv.find_all('a', {'class': 'z_h_81637'})
                if len(imageInfo):
                    content = str(imageInfo[0]).split('"')

                    photoPath = content[19][3:len(content[19])]
                    imageId = photoPath.split("-")[len(photoPath.split("-")) - 1]

                    discription = content[21].replace('\n', '').replace('\0', '').replace('\f', '').replace('\b', '').replace('\a', '').replace('\a', '"').strip()
                    if re.search(r'[^a-zA-Z]', discription):
                        imageInternetPath = "https://image.shutterstock.com" + photoPath + "-260nw-" + imageId + ".jpg"
                        imageContent = self.__loadImage(imageInternetPath, imageId)
                        if imageContent is not None:
                            imageLocalPath = self.__saveLocalImage(imageId, imageContent)
                            if imageLocalPath is not None:
                                success = self.__cropImageCharacter(imageLocalPath)
                                if success:
                                    self.__saveImageInfo(imageLocalPath, discription, imageInternetPath)
                                    newPageCount = self.__getPageCount(soup)
                                    if newPageCount != 0:
                                        pageCount = newPageCount

    def __loadPage(self, pageId):
        try:
            url = 'https://www.shutterstock.com/ru/search?image_type=photo&sort=newest&page=%d' % (pageId)

            request = urllib3.PoolManager(10, self.userAgent)
            response = request.urlopen('GET', url)

            if response.status == 200 and response.data:
                return response.data
            return None
        except:
            return None

    def __loadImage(self, path, imageId):
        try:
            response = requests.get(path, self.userAgent)

            if response.content and response.status_code == 200:
                return response.content
            return None
        except:
            return None

    def __saveLocalImage(self, imageId, content):
        try:
            path = self.imageFolderPath + imageId + ".jpg"
            if os.path.isfile(path):
                return None
            out = open(path, "wb")
            out.write(content)
            out.close()
            return path
        except:
            return None

    def __saveImageInfo(self, localImagePath, discription, internerImagePath):
        with open('shutterstockImages.tsv', 'a') as out_file:
            tsv_writer = csv.writer(out_file, delimiter='\t')
            tsv_writer.writerow([localImagePath, discription, internerImagePath])

    def __saveLoadedPageCount(self, cout):
        with open('loadedPageCount.tsv', 'wt') as out_file:
            tsv_writer = csv.writer(out_file, delimiter='\t')
            tsv_writer.writerow([cout])

    def __readLoadedPageCount(self):
        try:
            tsv_file = open("loadedPageCount.tsv")
            read_tsv = csv.reader(tsv_file, delimiter="\t")
            cout = int(list(read_tsv)[0][0])
            tsv_file.close()
            return cout
        except:
            return 0

    def __getInitPageCount(self):
        pageData = self.__loadPage(1)
        if pageData is not None:
            soup = BeautifulSoup(pageData, 'html.parser')
            return self.__getPageCount(soup)

    def __getPageCount(self, soup):
        pageCountDiv = soup.find('div', {'class': 'b_aI_c6506'})
        pageCount = str(pageCountDiv).split(" ")[2][0:len(str(pageCountDiv).split(" ")[2]) - 6].replace(u'\xa0', u'')

        if pageCount.isdigit():
            return int(pageCount)
        return 0

    def __cropImageCharacter(self, path):
        try:
            im = Image.open(path)
            img_width, img_height = im.size
            im_crop = im.crop((0, 0, img_width, img_height - 20))
            im_crop.save(path, quality=95)
            return True
        except:
            print("не удалось обрезать изображение", path)
            return False

shutterstockParser = ShutterstockParser(imageFolderPath="/Users/kirill/Desktop/image/")
shutterstockParser.parseAllPages()


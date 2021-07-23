import logging
# import urllib3
import requests
from bs4 import BeautifulSoup
import re
import csv
from PIL import Image
import os
import sys
import uuid

class ShutterstockParser:

    userAgent = {'user-agent': 'Mozilla/5.0 (Windows NT 6.3; rv:36.0) ..'}
    labelsFile = "labels.tsv"
    offsetFile = "loadedPageCount.tsv"
    otherDataSources = "data.txt"
    pageCount = 0
    loadedPageCount = 0
    imageFolderPath = ""
    startFromLastPage = True
    loadedImages = {}
    session = None

    def __init__(self, imageFolderPath, labelsFile=None, offsetFile=None, startFromLastPage=True):
        self.imageFolderPath = imageFolderPath
        if labelsFile:
            self.labelsFile = labelsFile
        if offsetFile:
            self.offsetFile = offsetFile
        self.startFromLastPage = startFromLastPage
        self.session = requests.Session()
        self.session.headers.update(self.userAgent)
        logging.info("Image folder: %s; labels file: %s; offset file: %s; go from last page to first: %s", self.imageFolderPath, self.labelsFile, self.offsetFile, self.startFromLastPage)

    def parseAllPages(self):
        self.__loadImageIds(self.imageFolderPath, self.labelsFile)
        if self.otherDataSources:
            with open(self.otherDataSources) as f:
                for line in f:
                    p = [x.strip() for x in line.strip().split(',')]
                    if len(p) > 1:
                        self.__loadImageIds(p[0], p[1])
                    else:
                        logger.warning("Unable to parse line %s from %s", line, self.otherDataSources)
        self.loadedPageCount = self.__readLoadedPageCount()
        logging.info("%d pages were already loaded", self.loadedPageCount)
        self.pageCount = self.__getInitPageCount()
        logging.info("Total %d pages are available for download", self.pageCount)
        while self.pageCount > self.loadedPageCount:
            if self.startFromLastPage:
                self.parsePage(self.pageCount - self.loadedPageCount)
            else:
                self.parsePage(self.loadedPageCount)
            self.loadedPageCount += 1
            self.__saveLoadedPageCount(self.loadedPageCount)

    def parsePage(self, pageId = 1):
        logging.info("Parsing page %d out of %d ...", pageId, self.pageCount)
        newImageCount = 0
        dupImageCount = 0
        pageData = self.__loadPage(pageId)
        if pageData is not None:
            soup = BeautifulSoup(pageData, 'html.parser')

            imageTables = soup.find_all('div', {'class': 'z_h_b900b'})
            for imageDiv in imageTables:
                imageInfo = imageDiv.find_all('a', {'class': 'z_h_81637'})
                if len(imageInfo):
                    content = str(imageInfo[0]).split('"')

                    photoPath = content[19]#[3:len(content[19])]
                    imageId = photoPath.split("-")[len(photoPath.split("-")) - 1]
                    # skip images that were already loaded
                    if imageId in self.loadedImages:
                        dupImageCount += 1
                        continue

                    description = content[21].replace('\n', ' ').replace('\t', ' ').replace('\0', ' ').replace('\f', ' ').replace('\b', ' ').replace('\a', ' ').replace('\r', ' ').strip()
                    # if re.search(r'[^a-zA-Z]', description):
                        # try:
                        #     imageInternetPath = imageInfo[0].img.get('src')
                        # except Exception:
                        #     logging.error("No image path found for image %s on page %d. Source: %s", imageId. pageId, imageInfo[0])
                        #     continue
                    imageInternetPath = "https://image.shutterstock.com" + photoPath + "-260nw-" + imageId + ".jpg"
                    imageContent = self.__loadImage(imageInternetPath, imageId)
                    if imageContent is not None:
                        imageLocalPath = self.__saveLocalImage(imageId, imageContent)
                        if imageLocalPath is not None:
                            success = self.__cropImage(imageLocalPath)
                            if success:
                                self.__saveImageInfo(imageLocalPath, description, imageInternetPath)
                                self.loadedImages[imageId] = imageLocalPath
                                newImageCount += 1
                                newPageCount = self.__getPageCount(soup)
                                if newPageCount != 0:
                                    self.pageCount = newPageCount
            logging.info("Page had %d elements. %d images were saved. %d images were downloaded earlier.", len(imageTables), newImageCount, dupImageCount)
        else:
            logging.warning("Empty page %d", pageId)

    def __loadPage(self, pageId):
        try:
            url = 'https://www.shutterstock.com/search?image_type=photo&sort=newest&page=%d' % (pageId)

            # request = urllib3.PoolManager(10, self.userAgent)
            # response = request.urlopen('GET', url)
            # if response.status == 200 and response.data:
            #     return response.data
            response = self.session.get(url)
            if response.status_code == 200 and response.content:
                return response.content
            logging.error("Page %d not loaded. Response code %s, content length %d", pageId, response.status_code, len(response.content))
            return None
        except Exception:
            logging.exception("Exception while loading page %d", pageId)
            return None

    def __loadImage(self, path, imageId):
        logging.info("Downloading image %s from %s", imageId, path)
        try:
            # response = requests.get(path, self.userAgent)
            response = self.session.get(path)

            if response.content and response.status_code == 200:
                return response.content
            logging.error("Failed to download image %s. Response code %s, content length %d", imageId, response.status_code, len(response.content))
            return None
        except Exception:
            logging.exception("Exception while loading image %s", imageId)
            return None

    def __saveLocalImage(self, imageId, content):
        try:
            path = os.path.join(self.imageFolderPath, f"{imageId}.jpg")
            if os.path.isfile(path):
                logging.warning("Can't save image %s as it already exists", imageId)
                return None
            out = open(path, "wb")
            out.write(content)
            out.close()
            return path
        except Exception:
            logging.exception("Unable to save image %s", imageId)
            return None

    def __saveImageInfo(self, localImagePath, description, internetImagePath):
        with open(self.labelsFile, 'a') as out_file:
            tsv_writer = csv.writer(out_file, delimiter='\t')
            tsv_writer.writerow([localImagePath, description, internetImagePath])

    def __saveLoadedPageCount(self, cout):
        with open(self.offsetFile, 'wt') as out_file:
            tsv_writer = csv.writer(out_file, delimiter='\t')
            tsv_writer.writerow([cout])

    def __readLoadedPageCount(self):
        try:
            tsv_file = open(self.offsetFile)
            read_tsv = csv.reader(tsv_file, delimiter="\t")
            cout = int(list(read_tsv)[0][0])
            tsv_file.close()
            return cout
        except:
            return 0

    def __getInitPageCount(self):
        pageData = self.__loadPage(1)
        # print(pageData)
        if pageData is not None:
            soup = BeautifulSoup(pageData, 'html.parser')
            return self.__getPageCount(soup)

    def __getPageCount(self, soup):
        pageCountDiv = soup.find('div', {'class': 'b_aI_c6506'})
        pageCount = str(pageCountDiv).split(" ")[2][0:len(str(pageCountDiv).split(" ")[2]) - 6].replace(u'\xa0', u'')
        pageCount = pageCount.replace(',', '')

        if pageCount.isdigit():
            return int(pageCount)
        return 0

    def __cropImage(self, path):
        try:
            im = Image.open(path)
            img_width, img_height = im.size
            im_crop = im.crop((0, 0, img_width, img_height - 20))
            im_crop.save(path, quality=95)
            return True
        except:
            logging.error("Unable to crop image %s", path)
            return False

    def __loadImageIds(self, path, labelsFile):
        logging.info("Loading image ids from %s", path)
        imageFiles = {}
        for entry in os.scandir(path):
            if entry.is_file() and entry.name.endswith('.jpg'):
                imageId, _ = os.path.splitext(entry.name)
                imageFiles[imageId] = entry.name
                if (len(imageFiles) % 100000) == 0:
                    logging.info("%d image files processed", len(imageFiles))
        logging.info("Total of %d image files were found", len(imageFiles))
        logging.info("Loading descriptions from %s", self.labelsFile)
        with open(labelsFile) as f:
            for line in f:
                p = [x.strip() for x in line.rstrip('\n').split('\t')]
                if len(p) < 1:
                    logging.warning("Unable to parse line %s", line)
                    continue
                imageId, _ = os.path.splitext(os.path.basename(p[0]))
                if imageId in imageFiles:
                    self.loadedImages[imageId] = imageFiles[imageId]
                    del imageFiles[imageId]
                else:
                    logging.warning("Description without a source image file %s", p[0])
        for imageId in imageFiles:
            logging.warning("Image file without description %s", imageFiles[imageId])
        logging.info("Total %d image ids loaded", len(self.loadedImages))


def main():
    logging_filename = f"{sys.argv[0]}_{sys.argv[1]}.log" if len(sys.argv) > 1 else f"{sys.argv[0]}.log"
    logging.basicConfig(
        handlers=[logging.StreamHandler(), logging.FileHandler(logging_filename)],
        level=logging.INFO,
        format="%(asctime)s %(name)s - %(levelname)s - %(message)s"
    )
    labelsFile = None
    offsetFile = None
    imageFolderPath = "images/"
    startFromLastPage = True
    if len(sys.argv) > 1:
        imageFolderPath = sys.argv[1]
    if len(sys.argv) > 2:
        labelsFile = sys.argv[2]
    if len(sys.argv) > 3:
        offsetFile = sys.argv[3]
    if len(sys.argv) > 4:
        startFromLastPage = (int(sys.argv[4])==1)
    shutterstockParser = ShutterstockParser(imageFolderPath=imageFolderPath, labelsFile=labelsFile, offsetFile=offsetFile, startFromLastPage=startFromLastPage)
    shutterstockParser.parseAllPages()



if __name__ == '__main__':
    main()

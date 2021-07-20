import os
import numpy as np
from PIL import Image, ImageChops

np.set_printoptions(threshold=10000000)

directory = "D:/final/photos"
name_files = os.listdir(directory)

size_files = []
for name in name_files:
    size_files.append(str(os.path.getsize(directory + '/' + name)))

size_and_name_files = np.column_stack((size_files, name_files))

size_and_name_files = sorted(size_and_name_files, key=lambda x: x[0])

flag_first = True
out_identical_photos = open('identical.tsv', 'w', encoding='utf-8')
identical_photos = []
result_identical_photos = []
count_of_identical_photos = 0
description_photos = open('D:/final/descriptionPhotos.tsv', 'r', encoding='utf-8')
lines_description = description_photos.readlines()

for i in range(len(size_and_name_files)):
    if not (i == len(size_and_name_files) - 1):
        if size_and_name_files[i][0] == size_and_name_files[i + 1][0]:
            if flag_first:
                out_identical_photos.write('\n' + size_and_name_files[i][1] + '\t' + size_and_name_files[i + 1][1])
                identical_photos.append(size_and_name_files[i][1])
                identical_photos.append(size_and_name_files[i + 1][1])
                flag_first = False
            else:
                identical_photos.append(size_and_name_files[i + 1][1])
                out_identical_photos.write('\t' + size_and_name_files[i + 1][1])
        else:
            flag_first = True
            if identical_photos:
                flag_excess_photos = np.zeros(len(identical_photos))
                for num_first_photo, first_photo in enumerate(identical_photos):
                    if not (num_first_photo == len(identical_photos) - 1):
                        for num_second_photo, second_photo in enumerate(identical_photos):
                            if num_second_photo > num_first_photo:
                                image_1 = Image.open(directory + '/' + first_photo)
                                image_2 = Image.open(directory + '/' + second_photo)
                                result = ImageChops.difference(image_1, image_2).getbbox()
                                if result is None:
                                    description_first = ''
                                    description_second = ''
                                    for line_first in lines_description:
                                        if line_first.find(first_photo) != -1:
                                            description_first = line_first.replace(first_photo, '')
                                            break
                                    for line_second in lines_description:
                                        if line_second.find(second_photo) != -1:
                                            description_second = line_second.replace(second_photo, '')
                                            break
                                    if description_first == description_second:
                                        flag_excess_photos[num_second_photo] = 1
                for num_item, item in enumerate(flag_excess_photos):
                    if item == 1:
                        result_identical_photos.append(identical_photos[num_item])
                        count_of_identical_photos += item
                identical_photos = []
                print(count_of_identical_photos)
result = open('result.tsv', 'w', encoding='utf-8')
for photo in result_identical_photos:
    result.write(photo + '\n')
print(len(result_identical_photos))
out_identical_photos.close()
description_photos.close()
result.close()

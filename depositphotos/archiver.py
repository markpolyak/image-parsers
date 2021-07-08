import os
import shutil

child_directory = 'D:/y'

counter = 0
while counter <= 998000:
    os.mkdir(child_directory + '/' + str(counter))
    counter += 2000

parent_directory = "D:/final/photos"
name_files = os.listdir(parent_directory)
count_photos = 0
child_folder = child_directory + '/' + str(count_photos)
for file in name_files:
    if count_photos % 2000 == 0:
        child_folder = child_directory + '/' + str(count_photos)
    shutil.copy(parent_directory + '/' + file, child_folder)
    count_photos += 1

archive_counter = 0
while archive_counter <= 998000:
    shutil.make_archive(child_directory + '/' + str(archive_counter), 'tar', child_directory + '/' + str(archive_counter))
    print(archive_counter)
    archive_counter += 2000

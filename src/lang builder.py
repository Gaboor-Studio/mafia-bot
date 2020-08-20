import os
import codecs
try:
    while True:
        file_name = input("Enter file name: ")
        with codecs.open(os.path.join("Lang", "en", file_name), 'w', encoding='utf8') as file:
            file.write(input("Enter english text: "))
        with codecs.open(os.path.join("Lang", "fa", file_name), 'w', encoding='utf8') as file:
            file.write(input("Enter persian text: "))
except KeyboardInterrupt:
    pass

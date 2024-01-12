import os
import time
from multiprocessing import Process
import easywebdav
easywebdav.basestring = str  # Python 3 fix
easywebdav.client.basestring = str  # Python 3 fix
import urllib

from lib.helper import get_timestamp


def log(message: str):
    msg = str(message)
    with open("log_upload_service.txt", "a") as file:
        file.write("------- " + get_timestamp() + ' -------\n')
        file.write(msg)
        file.write("\n\n")
    print(msg)


def upload():

    file_list = next(os.walk('upload-pool'))[2]

    # webdav connection settings
    host = os.environ['W_DOMAIN']
    username = os.environ['W_USERNAME']
    password = os.environ['W_PASSWORD']
    root_path = os.environ['W_ROOT_PATH']

    for file in file_list:
        print(f'Fileupload: {file}')
        try:
            webdav = easywebdav.connect(host=host, username=username, password=password, protocol='https')
            webdav.upload(f'upload-pool/{file}', f'{root_path}{file}')
            time.sleep(2)
            # verify upload
            webdav_file_list = webdav.ls(f"{root_path}")
            webdav_file_list = [urllib.parse.unquote(x.name).split('/')[-1] for x in webdav_file_list]

            if file in webdav_file_list:
                os.remove(f'upload-pool/{file}')
                log(f'Fileupload Success: True')
            else:
                log('Datei nach Upload nicht auf dem Server gefunden')
        except (Exception,) as e:
            log(e)
            print(e)


class UploadService:

    def __init__(self):
        self.upload_running = False

        # thread = Thread(target=self.service)
        # thread.start()
        p = Process(target=self.service)
        p.start()

    def service(self):
        while True:
            if not self.upload_running:
                print('Upload Service: Start')
                try:
                    upload()
                except (BaseException,) as e:
                    log(e)
                print('Upload Service: Done')
            time.sleep(60)

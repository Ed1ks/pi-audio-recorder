import os
import subprocess
import time
from datetime import datetime
from multiprocessing import Process
from typing import List
from mutagen.easyid3 import EasyID3

from lib.helper import get_timestamp


def log(message: str):
    msg = str(message)
    with open("log_convert_service.txt", "a") as file:
        file.write("------- " + get_timestamp() + ' -------\n')
        file.write(msg)
        file.write("\n\n")
    print(msg)


def convert():
    convert_pool_dir = 'convert-pool/'
    upload_pool_dir = 'upload-pool/'

    file_list: List[str] = next(os.walk('convert-pool'))[2]

    for file in file_list:

        output_file_name = file.replace(".wav", ".mp3")

        if file.lower().endswith('.wav'):
            input_file_stats = os.stat(convert_pool_dir + file)
            input_file_size = input_file_stats.st_size / (1024 * 1024)
            input_file_size_str = str(round(input_file_size, 2)) if input_file_size < 10 else str(
                round(input_file_size, 0))
            start_time = time.perf_counter()

            # löschen wenn Datei kleiner als 2 MB
            # if input_file_size < 2:
            #     os.remove(convert_pool_dir + file)
            #    continue
            print(f'Convert-Service: Convert File: {file} ({input_file_size_str}MB)')

            try:
                # convert
                # folgende bibliothek funktioniert nicht bei 500mb ram und 45min (330mb) wav aufnahmme:
                # sound = pydub.AudioSegment.from_wav(convert_pool_dir + file)
                # sound.export(f'{ convert_pool_dir }output.mp3', format="mp3")

                # deswegen direkt über ffmpeg:
                # https://trac.ffmpeg.org/wiki/Encode/MP3
                # -i = Inputdatei
                # -vn = Nur Audio
                # -ar 44100 = 44,1 kHz
                # -q:a 2 = 170-210 kB/s mp3 bitrate

                # in mp3 umwandeln
                cmd = f'ffmpeg -y -i "{convert_pool_dir + file}" -vn -ar 44100 -q:a 2 "{convert_pool_dir}output_bn.mp3"'
                return_value = subprocess.call(cmd, shell=True)
                print('convert success')

                if not return_value:
                    # Audio Lautstärke normalisieren:
                    print('Convert-Service: start audio-normalizing')
                    cmd = f'ffmpeg-normalize -c:a mp3 "{convert_pool_dir}output_bn.mp3" -o "{convert_pool_dir}output.mp3"'
                    return_value = subprocess.call(cmd, shell=True)

                success = False if return_value else True

                if not success:
                    print(f'Error while converting audio file {file}')
                    continue
                # inform
                output_file_stats = os.stat(convert_pool_dir + 'output.mp3')
                output_file_size = output_file_stats.st_size / (1024 * 1024)
                output_file_size_str = str(round(output_file_size, 2)) if output_file_size < 10 else str(
                    round(output_file_size, 0))

                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                duration_str = str(int(elapsed_time))
                msg = f'Successfully Converted to file {output_file_name} (Output Size: {output_file_size_str}MB - Conv. Duration: {duration_str} sec)'
                log(msg)
                os.remove(convert_pool_dir + file)
                # os.remove(convert_pool_dir + 'output_bn.mp3')

                # move file
                os.rename(f'{convert_pool_dir}output.mp3', f'{upload_pool_dir}{output_file_name}')

                # set metadata
                if len(output_file_name) >= 10:
                    date_str = output_file_name[:10]
                    print(date_str)
                    date_format = '%Y-%m-%d'
                    try:
                        date_obj = datetime.strptime(date_str, date_format)
                        date_str, year_str = date_obj.strftime('%Y.%m.%d'), date_obj.strftime('%Y')

                        # Liste der Tags: https://from-locals.com/python-mutagen-mp3-id3/
                        audio = EasyID3(f'{upload_pool_dir}{output_file_name}')
                        audio['title'] = f"{date_obj.strftime('%Y-%m-%d')} "
                        audio['organization'] = u"Freie Bibelgemeinde Worpswede"
                        audio['language'] = u"German"
                        audio['date'] = f"{date_str}"
                        audio['originaldate'] = f"{date_str}"
                        audio['website'] = u"https://freie-bibelgemeinde-worpswede.de/"
                        # audio['artist'] = u"Me"
                        # audio['album'] = u"My album"
                        # audio['composer'] = u""  # clear
                        audio.save()
                    except (BaseException,) as e:
                        log(e)
            except (Exception,) as e:
                log(e)


class AudioConvertService:

    def __init__(self):
        self.convert_running = False

        # thread = Thread(target=self.service)
        # thread.start()
        p = Process(target=self.service)
        p.start()

    def service(self):
        while True:
            if not self.convert_running:
                print('Audio Convert Service: Start')
                try:
                    convert()
                except (BaseException,) as e:
                    log(e)
                print('Audio Convert Service: Done')
            time.sleep(60)

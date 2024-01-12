import os
import pathlib
import platform
import signal
import subprocess
import sys
import time
import traceback
from multiprocessing import freeze_support
from dotenv import load_dotenv  # in Windows: pip install python-dotenv

from lib.helper import get_timestamp

# Arbeitsordner setzen (weil es beim debuggen falsch ist)
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.getcwd())
sys.path.append(os.path.dirname('lib/'))

from lib.Recorder import Recorder
from lib.UploadService import UploadService
from lib.AudioConvertService import AudioConvertService

# install_all_dependencies_if_not_exists()

from pynput import keyboard


class handler(keyboard.Listener):

    def __init__(self):
        super().__init__(on_release=self.on_release)
        self.recorder = None
        self.pause = False

        try:
            self.init_recorder()
        except IOError as e:
            print(e)
        self.recording = False

    def init_recorder(self):
        self.recorder = Recorder(wavfile="mic.wav")
        return self.recorder

    def on_release(self, key):
        if key is None:  # unknown event
            pass
        elif isinstance(key, keyboard.KeyCode):  # special key event
            if key.char == 'a':  # start recording
                if self.pause:
                    # -- continue recording, stop pause --
                    self.pause = False
                    self.recorder.stream.start_stream()
                    print('Aufnahme fortgesetzt')
                elif self.recording:
                    # -- pause --
                    self.pause = True
                    self.recorder.stream.stop_stream()
                    print('Aufnahme pausiert')
                else:
                    # -- Start record --
                    # überprüfen ob eine übriggebliebene Aufnahme existiert und in den Upload Ordner verschieben
                    if os.path.isfile('mic.wav'):
                        os.rename('mic.wav', f'convert-pool/leftover_file_{get_timestamp()}.wav')

                    try:
                        # Sicherstellen, dass alles ok ist
                        if self.recorder is None:
                            self.recorder = self.init_recorder()

                        # starte Aufnahme
                        self.recorder.start()
                        self.recording = True
                        print('Aufnahme gestartet')
                    except (Exception,):
                        self.recorder = None
                        self.recording = False
                        self.pause = False
                        if os.path.isfile('mic.wav'):
                            try:
                                os.remove("mic.wav")
                            except (Exception, ) as e:
                                print(e)
                        print('Kein Mikrophon angeschlossen')
            if key.char == 's':  # stop recording
                self.pause = False
                # -- stop recording --
                if self.recording:
                    print('Aufnahme beendet')
                    self.recording = False
                    self.recorder.stop()
                    self.recorder = None
                    time.sleep(0.5)
                    if os.path.isfile('mic.wav'):
                        os.rename('mic.wav', f'convert-pool/{get_timestamp()}.wav')


def kill_duplicate_execution():
    os_name = platform.system()
    print(f'OS Detected: {os_name}')

    if os_name == 'Linux':
        # Doppelte Prozesse unter Linux beenden (z.B. beim Debuggen)
        current_pid = os.getpid()
        current_file_name = str(os.path.basename(__file__))

        p = subprocess.Popen('ps -ef | grep python', shell=True, stdout=subprocess.PIPE, text=True)
        out, err = p.communicate()

        for line in out.splitlines():
            if current_file_name in line:
                pid = None
                # pid = int(line.split(None, 1)[0])
                for i, value in enumerate(line.split(' ')):
                    if i > 0 and value != '':
                        if value.isnumeric():
                            pid = int(value)
                            break
                if pid is not None and pid != current_pid:
                    os.kill(pid, signal.SIGKILL)


# Fehler in log speichern
def log_exceptions(err_type, value, tb):
    f = open("../../Desktop/dev/log.txt", "a")
    f.write("------- " + get_timestamp() + ' -------\n')
    for line in traceback.TracebackException(err_type, value, tb).format(chain=True):
        f.write(line)
    f.write("\n\n")
    f.close()

    sys.__excepthook__(err_type, value, tb)


sys.excepthook = log_exceptions

if __name__ == '__main__':
    freeze_support()
    load_dotenv()
    # falls skript bereits ausgeführt wird, andere Prozesse beenden
    kill_duplicate_execution()

    # Benötigte Order erstellen
    pathlib.Path('upload-pool').mkdir(parents=True, exist_ok=True)
    pathlib.Path('convert-pool').mkdir(parents=True, exist_ok=True)

    handler = handler()
    handler.start()  # keyboard listener is a thread so we start it here
    # handler.join()  # wait for the tread to terminate so the program doesn't instantly close

    print('a = start/pause recording')
    print('s = stop recording')

    upload_service = UploadService()
    audio_convert_service = AudioConvertService()

    print('Everything done - lets go sleep')

    while True:
        if handler.recorder is not None:
            recording_elapsed_time = handler.recorder.get_record_elapsed_time()
            if recording_elapsed_time is not None:
                if recording_elapsed_time >= 60 * 60 * 2:
                    handler.recorder.stop()
                # print(f'recording time: { recording_elapsed_time }')
        time.sleep(10)

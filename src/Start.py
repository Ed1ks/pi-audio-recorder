import os
import pathlib
import signal
import subprocess
import sys
import time
import traceback
from multiprocessing import freeze_support
from threading import Thread
from dotenv import load_dotenv

from lib.helper import get_timestamp

# Arbeitsordner setzen (weil es beim debuggen falsch ist)
os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.getcwd())
sys.path.append(os.path.dirname('lib/'))

from lib.Recorder import Recorder
from lib.UploadService import UploadService
from lib.AudioConvertService import AudioConvertService

# install_all_dependencies_if_not_exists()

from gpiozero import LED, Button


class handler:

    def __init__(self, gpio_led: LED, gpio_button: Button):
        self.gpio_led = gpio_led
        self.gpio_button = gpio_button
        self.recorder = None
        self.pause = False

        try:
            self.init_recorder()
        except IOError:
            error_blink(gpio_led)

        self.recording = False

    def init_recorder(self):
        self.recorder = Recorder(wavfile="mic.wav")
        return self.recorder

    def button_pressed(self):
        button_was_held = False
        print('PRESSED!')
        if self.gpio_button.is_active:
            # 2 Sekunden gedrückt halten = Aufnahme beenden
            start_time = time.perf_counter()
            while button.is_active:
                end_time = time.perf_counter()
                elapsed_time = end_time - start_time
                if elapsed_time > 1:
                    button_was_held = True
                    self.gpio_led.off()
                    # -- stop pause --
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
                    return

            if not button_was_held:
                if self.pause:
                    # -- continue recording, stop pause --
                    self.pause = False
                    self.recorder.stream.start_stream()
                    self.gpio_led.on()
                    print('Aufnahme fortgesetzt')
                elif self.recording:
                    # -- pause --
                    self.pause = True
                    self.recorder.stream.stop_stream()
                    thread = Thread(target=lambda: self.pause_blink(gpio_led=led))
                    thread.start()
                    print('Aufnahme pausiert')
                else:
                    # -- Start record --
                    # überprüfen ob eine übriggebliebene Aufnahme existiert und in den Upload Ordner verschieben
                    if os.path.isfile('mic.wav'):
                        os.rename('mic.wav', f'convert-pool/leftover_file_{get_timestamp()}.wav')

                    try:
                        # Sicherstellen, dassalles ok ist
                        if self.recorder is None:
                            self.recorder = self.init_recorder()

                        # starte Aufnahme
                        self.recorder.start()
                        self.gpio_led.on()
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
                                print (e)
                        print('Kein Mikrophon angeschlossen')
                        error_blink(gpio_led=led)

    def pause_blink(self, gpio_led: LED):
        while self.pause:
            if self.pause:
                gpio_led.on()
                time.sleep(1)
            if self.pause:
                gpio_led.off()
                time.sleep(1)


def startup_blink(gpio_led: LED):
    gpio_led.on()
    time.sleep(2)
    gpio_led.off()


def error_blink(gpio_led: LED):
    for _ in range(10):
        gpio_led.on()
        time.sleep(0.15)
        gpio_led.off()
        time.sleep(0.15)


def kill_duplicate_execution():
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

    # BCM-Nummerierung verwenden (Pin nummern verwenden)
    # Schaltung:
    # 3.3V (Pin 01) - Rot
    # Ground (Pin 09) - Schwarz

    # GPIO 17 (Pin 11) als Ausgang setzen für LED - Grün
    led = LED(17)
    led.off()
    # GPIO 22 (Pin 15) als Ausgang setzen für Button - Blau
    button = Button(22, pull_up=False, bounce_time=0.05)

    # zeige Lebenszeichen
    startup_blink(led)

    handler = handler(led, button)
    button.when_activated = handler.button_pressed
    # GPIO.add_event_detect(27, GPIO.RISING, callback=handler.my_callback, bouncetime=300)

    upload_service = UploadService()
    audio_convert_service = AudioConvertService()

    # verschiebe übrig gebliebene wav
    if os.path.isfile('mic.wav'):
        os.rename('mic.wav', f'convert-pool/{get_timestamp()}.wav')

    print('Everything done - lets go sleep')
    while True:
        if handler.recorder is not None:
            recording_elapsed_time = handler.recorder.get_record_elapsed_time()
            if recording_elapsed_time is not None:
                if recording_elapsed_time >= 60 * 60 * 2:
                    handler.recorder.stop()
                # print(f'recording time: { recording_elapsed_time }')
        time.sleep(10)

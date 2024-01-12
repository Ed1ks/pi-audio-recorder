import time

import pyaudio
import wave


class Recorder:
    def __init__(self, wavfile):
        # Gute Info-Seite für die Einstellungen: https://www.baumannmusic.com/de/2012/sampleratehz-und-khz-aufloesung-bit-und-bitrate-kbits/

        self.py_audio = pyaudio.PyAudio()
        try:
            input_device_info = self.py_audio.get_default_input_device_info()
        except (Exception,):
            # sofort beenden, sonst wird ein anschließender Mikrofonanschluss nicht erkannt
            self.py_audio.terminate()
            raise IOError

        self.wf = None
        self.stream = None
        self.filename = wavfile
        # self.channels = 2 if input_device_info['maxInputChannels'] >= 2 else 1
        self.channels = 1  # mono

        # 16-bit Music CD
        # 24/32-bit Studio
        self.dataformat = pyaudio.paInt16

        # 44100 (44,1 kHz Musik CD)
        # 48000 (48,0 kHz Film)
        # 96000 (96,0 kHz Studio)
        self.sample_rate = 44100
        self.chunksize = int(0.03 * self.sample_rate)  # vorher: 8192
        self.recording = False
        self.recording_start_time = time.perf_counter()

    def start(self):
        # we call start and stop from the keyboard listener, so we use the asynchronous
        # version of pyaudio streaming. The keyboard listener must regain control to
        # begin listening again for the key release.
        if not self.recording:
            self.wf = wave.open(self.filename, 'wb')
            self.wf.setnchannels(self.channels)
            self.wf.setsampwidth(self.py_audio.get_sample_size(self.dataformat))
            self.wf.setframerate(self.sample_rate)

            def callback(in_data, frame_count, time_info, status):
                # file write should be able to keep up with audio data stream (about 1378 Kbps)
                self.wf.writeframes(in_data)
                return in_data, pyaudio.paContinue

            self.stream = self.py_audio.open(format=self.dataformat,
                                             channels=self.channels,
                                             rate=self.sample_rate,
                                             input=True,
                                             stream_callback=callback)
            self.stream.start_stream()
            self.recording = True
            print('recording started')

    def stop(self):
        if self.recording:
            self.stream.stop_stream()
            self.stream.close()
            self.wf.close()

            self.recording = False
            self.py_audio.terminate()
            print('recording finished')

    def get_record_elapsed_time(self):
        if self.recording:
            end_time = time.perf_counter()
            elapsed_time = end_time - self.recording_start_time
            return elapsed_time
        else:
            return None

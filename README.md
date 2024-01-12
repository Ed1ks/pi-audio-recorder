# pi-audio-recorder
## Funktion

Über GPIO wird der Raspberry mit einem Button angesteuert. Dies startet eine Audioaufnahme und der Button leuchtet während der Aufnahme.


### Tastenfunktion:
drücken = Aufnahme starten / pausieren

halten = Aufnahme beendet

### Leuchte:
dauerhaftes Leuchten = Aufnahme

langsames Blinken = Pause

schnelles blinken = Fehler (wenn kein Mikrofon bei Aufnahmestart gefunden wird)


## Hardware
* Minimum Raspberry Pi Zero 2W
* Ein Knopf mit Leuchte z.B. [diesen bei Amazon](https://www.amazon.de/dp/B07GB6Y1SZ?psc=1&ref=ppx_yo2ov_dt_b_product_details)

### Schaltung:
![Schaltung.png](assets/Schaltung.png)

# Develope

## Beschreibung
Die temporäre Datei "mic.wav" ist während der Aufnahme im root Ordner.

Es werden zu Beginn 2 weitere Subprozesse gespawnt, die die Ordner "convert-pool", "upload-pool" alle 60 Sekunden auf Dateien prüfen.

Ist eine Audioaufnahme beendet, wird "mic.wav" in <Zeitstempel>.wav umbenannt und in den convert-pool verschoben.
Wenn der ConvertService die Datei findet, konvertiert er die .wav datei in eine .mp3 Datei und verschiebt diese Datei in den Upload-Pool.

Wenn der UploadService die .mp3 in seinem Ordner findet, wird die Datei über WebDAV in die Cloud hochgeladen.

Wird die Aufnahme unerwartet unterbrochen, so wird beim nächsten Aufnahme-Start die übriggebliebene .wav Datei nicht überschrieben, sonder als leftover_<zeitstempel> umbennant und ebenfalls in den Convert-Pool geschoben.

## Einen Raspberry einrichten (ohne docker):
1. Raspbian OS Lite (32-bit) auf eine SD Karte installieren und SSH aktivieren. (Raspberry Pi Imager verwenden)
2. Leere Datei namens "ssh" im root erstellen 
3. Die Dateien dieses Projektes über SFTP in den Ordner "home/pi/RaspAudioRecorder/" vom Raspberry kopieren.
4. > sudo apt -y install ffmpeg python3-pynput python3-pyaudio python3-gpiozero python3-easywebdav python3-mutagen python3-dotenv
5. > sudo apt -y install python3-pip && sudo pip install ffmpeg-normalize --break-system-packages
6. > sudo apt -y update && sudo apt -y dist-upgrade && sudo apt -y clean
7. Autostart erstellen, damit der Skript beim Hochfahren automatisch gestartet wird:

   (Nano nutzen)
    > crontab -e
    
    ganz unten einfügen:

    > @reboot python "RaspAudioRecorder/Start.py" & 

    Mit Texteditor Nano mit CTRL + O, Enter abspeichern

    MIT CTRL + X verlassen
8. Skript manuell ausführen zum testen:
   > python "RaspAudioRecorder/Start.py"
9. > sudo reboot
   
## Einen Raspberry einrichten (mit docker) z.B. für Raspberry Pi 5
1. Raspberry Pi Os 64 bit ohne Desktop auf SD Karte flashen
2. Leere Datei namens "ssh" im root erstellen. Ggf. "wpa_supplicant.conf" Datei im Root erstellen oder hinein kopieren.
3. > sudo apt-get -y update && sudo apt-get -y upgrade && curl -fsSL https://get.Docker.com -o get-Docker.sh && sudo sh get-Docker.sh

   > sudo usermod -aG docker $USER && newgrp docker

   > sudo docker volume create portainer_data && docker run -d -p 8000:8000 -p 9443:9443 --name portainer --restart=always -v /var/run/docker.sock:/var/run/docker.sock -v portainer_data:/data portainer/portainer-ee:latest
4. Im Browser öffnen und registrieren: https://[ip of raspberry]:9443


## SSH Debug
-> Mit VScode (Kostenlos)

-> Mit Pycharm Professional (Teuer)
1. Verbindung herstellen mit SSH (Putty muss installiert sein, falls key benutzt wird. Und private key muss im puttygen sein (dafür einfach key öffnen))
2. Run -> Edit Configurations... -> Lokalen Ordner und Remote Ordner für Sync auswählen ![path-mapping.png](assets/path-mapping.png)

## Python Dependencies:
* python3-pip
* ffmpeg-normalize
* pynput
* pyaudio
* wave
* gpiozero
* easywebdav
* mutagen
* dotenv

## weitere Dependencies
* ffmpeg

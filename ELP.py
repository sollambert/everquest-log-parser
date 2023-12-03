import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import pyttsx3
import yaml
import os

tts_engine = pyttsx3.init()

def speak(text):
    tts_engine.say(text)
    tts_engine.runAndWait()

def on_modified(event):
    #open file from event
    with open(event.src_path, 'rb') as f:
        #seek to EOF
        try:
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b'\n':
                f.seek(-2, os.SEEK_CUR)
        except OSError:
            f.seek(0)
        #get the last line of file and remove timestamp
        last_line = f.readline().decode().split('] ', 1)[1]
        #print last line in file
        print(last_line)

def main() -> int:
    #load configuration
    config = {}
    with open("config.yaml", "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    print(config["rules"])

    speak("Testing")

    #initialize and configure watchdog
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    event_handler = PatternMatchingEventHandler(patterns=config["tracked_files"])
    event_handler.on_modified = on_modified
    observer = Observer()
    for path in config["paths"]:
        observer.schedule(event_handler, path, recursive=False)
    observer.start()

    #begin watchdog loop
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    return 0

if __name__ == '__main__':
    sys.exit(main())
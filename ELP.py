import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import pyttsx3
import yaml
import os

tts_engine = pyttsx3.init()
config = {}

def speak(text):
    tts_engine.say(text)
    tts_engine.runAndWait()

def peek(arr, index):
    if index < len(arr):
        return arr[index]
    return None

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
        for rule in config["rules"]:
            if config["rules"][rule]["pattern"] in last_line:
                if config["rules"][rule]["target"]:
                    target = config["rules"][rule]["target"]
                    if (config["rules"][rule]["target"] != "*"
                    and config["rules"][rule]["target"] not in last_line):
                        return
                if config["rules"][rule]["spell"]:
                    spell = config["rules"][rule]["spell"]
                    if (config["rules"][rule]["spell"] != "*"
                    and config["rules"][rule]["spell"] not in last_line):
                        return
                key = config["rules"][rule]["key"].split()
                last_line = last_line.split()
                keys = {}
                key_index = 0
                for i in range(len(last_line)):
                    next = peek(key, key_index + 1)
                    if key[key_index] != last_line[i]:
                        new_key = key[key_index][1:]
                        new_key = key[key_index][1:key[key_index].index('}')]
                        print(new_key)
                        if new_key not in keys:
                            keys[new_key] = []
                        if next != last_line[i]:
                            keys[new_key].append(last_line[i])
                            print(last_line)
                            print(key)
                            key_index -= 1
                        else:
                            key_index += 1
                    key_index += 1
                print(keys)
                #print last line in file
                target = ""
                spell = ""
                if "target" in keys:
                    target = " ".join(keys["target"])
                if "spell" in keys:
                    spell = " ".join(keys["spell"])
                output = config["rules"][rule]["text"].format(target=target, spell=spell)
                print(output)
                speak(output)

def main() -> int:
    #load configuration

    speak("Testing")

    #initialize and configure watchdog
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')
    event_handler = PatternMatchingEventHandler(patterns=config["tracked_files"])
    event_handler.on_modified = on_modified
    observer = Observer()

    #schedule given paths to be tracked by observer
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
    with open("config.yaml", "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    sys.exit(main())
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
is_speaking = False
queue = ["ELP activated"]

def peek(arr, index):
    if index < len(arr):
        return arr[index]
    return None

def on_speak_start():
    is_speaking = True

def on_speak_end():
    is_speaking = False

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
        try:
            last_line = f.readline().decode().split('] ', 1)[1]       
            #iterate through rules to check against last line of log file
            for rule in config["rules"]:
                #check if pattern exists in last line of log file
                if config["rules"][rule]["pattern"] in last_line:
                    #check if target exists in rule, if so ensure it exists within last line
                    if "target" in config["rules"][rule]:
                        target = config["rules"][rule]["target"]
                        if (config["rules"][rule]["target"] != "*"
                        and config["rules"][rule]["target"] not in last_line):
                            return
                    #check if spell exists in rule, if so ensure it exists within last line
                    if "spell" in config["rules"][rule]:
                        spell = config["rules"][rule]["spell"]
                        if (config["rules"][rule]["spell"] != "*"
                        and config["rules"][rule]["spell"] not in last_line):
                            return
                    #split rule key into individual words
                    key = config["rules"][rule]["key"].split()
                    last_line = last_line.split()
                    keys = {}
                    key_index = 0
                    for i in range(len(last_line)):
                        next = peek(key, key_index + 1)
                        if key[key_index] != last_line[i]:
                            new_key = key[key_index][1:]
                            new_key = key[key_index][1:key[key_index].index('}')]
                            if new_key not in keys:
                                keys[new_key] = []
                            if next != last_line[i]:
                                keys[new_key].append(last_line[i])
                                key_index -= 1
                            else:
                                key_index += 1
                        key_index += 1
                    target = ""
                    spell = ""
                    if "target" in keys:
                        target = " ".join(keys["target"])
                    if "spell" in keys:
                        spell = " ".join(keys["spell"])
                    if "ignored_spells" in config["rules"][rule]:
                        ignored_spells = config["rules"][rule]["ignored_spells"]
                        for ignored_spell in config["rules"][rule]["ignored_spells"]:
                            if spell == ignored_spell:
                                return
                    if "ignored_targets" in config["rules"][rule]:
                        ignored_targets = config["rules"][rule]["ignored_targets"]
                        for ignored_target in config["rules"][rule]["ignored_targets"]:
                            if target == ignored_target:
                                return
                    output = config["rules"][rule]["text"].format(target=target, spell=spell)
                    if output not in queue:
                        queue.append(output)
        except:
            print("Error reading end of file.")
 
def main() -> int:
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
            if len(queue) > 0 and not is_speaking:
                tts_engine.say(queue[0])
                tts_engine.runAndWait()
                queue.pop(0)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    return 0

if __name__ == '__main__':
    # load config
    tts_engine.connect("started_utterance", on_speak_start)
    tts_engine.connect("finished_utterance", on_speak_end)
    with open("config.yaml", "r") as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    sys.exit(main())
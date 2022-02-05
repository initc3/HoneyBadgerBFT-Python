import os
LOG_DIR = "./logs"
LOG_PATH = LOG_DIR + "/test_log.txt"
def log(msg):
    print(msg)
    msg += "\n"
    if not os.path.isdir(LOG_DIR):
        os.mkdir(LOG_DIR)
    with open(LOG_PATH, 'a') as f:
        f.write(msg)

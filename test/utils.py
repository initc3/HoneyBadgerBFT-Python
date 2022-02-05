LOG_PATH = "./test_log.txt"
def log(msg):
    print(msg)
    with open(LOG_PATH, 'a') as f:
        f.write(msg)

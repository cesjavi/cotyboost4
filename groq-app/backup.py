import shutil
import datetime
import os

def make_backup(src="backend", dest="backups"):
    os.makedirs(dest, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    shutil.make_archive(f"{dest}/backup_{timestamp}", 'zip', src)

if __name__ == "__main__":
    make_backup()

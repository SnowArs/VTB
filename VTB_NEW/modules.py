import os

def find_latest_file(path):
    files = os.listdir(path)
    if files:
        files = [os.path.join(path, file) for file in files]
        files = [file for file in files if os.path.isfile(file)]

        latest_file = max(files, key=os.path.getatime)
        return latest_file
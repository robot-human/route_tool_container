import os
import time
import subprocess

LOOP = True
DOWNLOAD = False

subscribe_file_path = f'./server_subscribe.py'
publish_file_path = f'./server_publish.py'
validation_file_path = f'./input_validation.py'
download_file_path = f'./download.py'
main_file_path = f'./route_main.py'


if __name__ == '__main__':
    if(DOWNLOAD):
        subprocess.run(f'python3 {download_file_path}',shell=True)
    else:
        while(LOOP):
            subprocess.run(f'python3 {subscribe_file_path}',shell=True)
            subprocess.run(f'python3 {validation_file_path}',shell=True)
            subprocess.run(f'python3 {main_file_path}',shell=True)
            time.sleep(1)
            subprocess.run(f'python3 {publish_file_path}',shell=True)
            time.sleep(0.5)
            #LOOP=False
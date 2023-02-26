# 引数がpytestならば関数pytestを実行し、startならば関数startを実行する
import os
import subprocess

def pytest():
    subprocess.run(["docker-compose", "build"])
    subprocess.run(["docker-compose", "up", "-d"])
    subprocess.run(["docker", "exec", "a_plus_tsukuba-web-1", "pytest"])

def start():
    subprocess.run(["docker-compose", "build"])
    subprocess.run(["docker-compose", "up", "-d"])
    subprocess.run(["docker", "stop", "a_plus_tsukuba-web-1"])

if __name__ == '__main__':
    import sys
    if sys.argv[1] == 'pytest':
        pytest()
    elif sys.argv[1] == 'start':
        start()
    else:
        print('argument error')
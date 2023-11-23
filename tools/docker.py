# @nitoca用？便利スクリプト

# 引数がpytestならば関数pytestを実行し、dbonlyならば関数dbonlyを実行する
import subprocess
import sys

def pytest():
    subprocess.run(["docker", "exec", "a_plus_tsukuba-web", "pytest"])

def dbonly():
    subprocess.run(["docker compose", "up", "-d", "--build"])
    subprocess.run(["docker", "stop", "a_plus_tsukuba-web"])

def stop():
    subprocess.run(["docker", "stop", "a_plus_tsukuba-web"])
    subprocess.run(["docker", "stop", "a_plus_tsukuba-db"])

if __name__ == '__main__':
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if arg == "pytest" :
        print("Running pytest IN CONTAINER...")
        pytest()
    elif arg == "dbonly" :
        print("Running the DB CONTAINER ONLY (stop the web container)...")
        dbonly()
    elif arg == "stop" :
        print("Stop containers...")
        stop()
    else:
        print("argument error")
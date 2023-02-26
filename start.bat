

# 引数がpytestの時とstartの時で処理を分ける
if [ $1 = "pytest" ]; then
    docker-compose build
    docker-compose up -d
    docker exec a_plus_tsukuba-web-1 pytest
elif [ $1 = "start" ]; then
    docker-compose build
    docker-compose up -d
    docker stop a_plus_tsukuba-web-1
fi
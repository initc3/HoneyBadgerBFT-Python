#!/bin/bash
echo "Killing running dockers"
kill -9 `ps | grep docker-compose | awk '{print $1}'`
sleep 1
echo "Running docker"
docker-compose run honeybadger >/dev/null 2>/dev/null &
sleep 1
echo "Running my_test.py"
docker exec -it `docker ps | tail -n 1 | awk '{print $1}'` /bin/bash -c "python our_tests/my_test.py"
echo "Done!"

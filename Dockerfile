FROM ubuntu:23.10

RUN apt update && apt install python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools python3-venv -y
COPY . .

RUN chmod +x docker_entry.sh

ENTRYPOINT ["/docker_entry.sh"]

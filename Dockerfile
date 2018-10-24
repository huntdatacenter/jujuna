FROM python:3.7

LABEL description="Install jujuna and its dependencies."

# Building container with jujuna command:
# docker build -t hunt/jujuna:0.1.0 -t hunt/jujuna:latest .
# Example run:
# docker run -v ~/.local/share/juju:/root/.local/share/juju -it hunt/jujuna:latest jujuna --help
# ~/.local/share/juju is mounted as a volume to provide credentials for connecting to juju

# Copy and install requirements first to use of cache
# will be skipped if requirements.txt has not changed
COPY requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

# Copy the rest of project and install jujuna, remove after install
COPY . /jujuna
RUN pip3 install /jujuna && rm -r /jujuna

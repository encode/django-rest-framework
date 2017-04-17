FROM python:2.7

ADD . /source
WORKDIR /source

RUN pip install tox
RUN pip install -r requirements.txt
RUN pip install --upgrade "Django<1.9"

CMD bash

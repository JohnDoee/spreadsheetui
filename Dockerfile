FROM python:3.7

ENV PYTHONUNBUFFERED 1

COPY requirements.txt /
RUN pip install -r /requirements.txt

RUN mkdir /code
COPY setup.py /code/
COPY MANIFEST.in /code/
COPY README.rst /code/
COPY main/ /code/main/
COPY spreadsheetui/ /code/spreadsheetui/
COPY twisted/ /code/twisted/

COPY --from=johndoee/spreadsheetui-webinterface:latest /dist/ /code/spreadsheetui/static/

WORKDIR /code
RUN python setup.py sdist
RUN cp /code/dist/*.tar.gz /
RUN pip install .

WORKDIR /

RUN rm -r /code
RUN mkdir /spreadsheetui

EXPOSE 18816

VOLUME ["/spreadsheetui"]
WORKDIR /spreadsheetui

CMD ["twistd", "-n", "spreadsheetui"]

FROM python:3.8.5
RUN pip install --upgrade pip
COPY . /
EXPOSE 5000
RUN pip install -r requirements.txt
CMD [ "python", "browser_code_executor/main.py"]

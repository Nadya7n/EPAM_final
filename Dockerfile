FROM python:3.8.5
COPY . /
EXPOSE 5000
RUN pip install -r requirements.txt
CMD ["python", "browser_code_executor/main.py"]

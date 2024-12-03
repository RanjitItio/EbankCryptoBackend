FROM python:3.12.7

WORKDIR /EbankcryptoAPI

COPY .requirements.txt /EbankcryptoAPI/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /EbankcryptoAPI/requirements.txt


COPY ./app /EbankcryptoAPI/app 


CMD ["uvicorn", "run", "app/main.py", "--port", "80", "--proxy-headers"]
FROM python:3.10.5
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh
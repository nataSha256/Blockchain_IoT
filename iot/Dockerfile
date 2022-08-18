FROM python:3.10.5
ADD client.py .
ADD apartment2016.csv .
RUN pip install pandas
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh
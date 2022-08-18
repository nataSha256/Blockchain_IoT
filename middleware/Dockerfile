FROM python:3.10.5
WORKDIR /middleware
COPY . .
RUN pip install web3 py-solc-x
RUN python installsolc.py
EXPOSE 4000
EXPOSE 4001
CMD ["python", "server.py"]
# Blockchain_Challenge_N
A blockchain based sensor data integration and user notification system.


## Solution Description

![System architecture image](/System_architecture.png)

The system consists of four logical parts:
1. IoT
2. Middleware
3. Ethereum blockchain 
4. User

The project is made in Python using Flask web framework and Web3.py library for interacting with Ethereum. 

The Ropsten testnetwork was chosen as the Ethereum blockchain, and to connect to it - the remote node provider Infura. The [Containerized Stage 2 (local, Ganache)](https://github.com/abTuhh/Blockchain_Challenge_N/commit/f85ef91ef2fadcda5db4e6c4297916dd976189b0) commit also allows to run the system version when it interacts not with Ropsten, but with the Ganache local network (represented by a separate Docker image *trufflesuite/ganache-cli*).

When the system started, a [wait-for-it](https://github.com/vishnubob/wait-for-it) script was used to check the availability of a host and TCP port (that is, the other part is already ready for interaction).


### IoT
- simulates data flow from sensors:
    - [UMass Smart* Dataset - 2017 release](https://traces.cs.umass.edu/index.php/Smart/Smart) (apartment-weather.tar.gz, apartment2016.xlsx) was used;
    - data is taken “from 11 sensors” at a time (1 row of dataset);
    - the data from each sensor is a record with the following fields: current date-time, parameter (for example, temperature or humidity) and the value of this parameter
    - the speed of the "polling" of the sensors is adjustable;
- sends these signals to the middleware part.

### Middleware
- interacts with the IoT part:
     - takes data from the IoT part
- interacts with the blockchain:
     - if necessary, deploys a smart contract in Ethereum
     - filters the data, and only adds filtered data to the blockchain
- interacts with the User part:
    - if the user part does not have information about the smart contract (its abi and address), - sends them 
     - receives parameters for filtering data from the user and implements them

### Ethereum blockchain
- interacts with the Middleware part:
    - smart contract can be deployed
    - the setData method of the smart contract can be called to write new data "from the sensor"
- interacts with the User part:
    - the IotData event of a smart contract can be read - both to display data already written, and to keep track of new data being added

### User
- interacts with the Middleware part:
     - if it does not have information about the smart contract (its abi and address), it asks the middleware to send and then receives them
     - sets parameters for filtering the data before it is forwarded to the blockchain
- interacts with the blockchain:
     - it is possible to set the number of last blocks to load data
     - visualizes data from the blockchain
     - keeps track of new smart contract events and, if any (i.e. new data items have been added to the blockchain), sends notifications and allows to view these new incoming items separately


## Starting, running and testing the system

### Quick start using Docker

Clone the repo and change to the directory:
```
git clone https://github.com/abTuhh/Blockchain_Challenge_N.git && cd Blockchain_Challenge_N
```
Then run containers: 
```
docker compose up –d
```
After that you can connect to the user interface: http://127.0.0.1:5000/ and you can also check the current incoming transactions for interaction with the smart contract in [Etherscan](https://ropsten.etherscan.io/address/0xf8fe858464629f80c89f78e2b59798c09635a33b) (the smart contract address is stored in a separate `IoT_address.txt` file, and it can be found both in the `/middleware` folder and in the `/user` folder).

If IoT and User do not start at startup with the error `/usr/bin/env: 'bash\r': No such file or directory`, [check](https://docs.github.com/en/get-started/getting-started-with-git/configuring-git-to-handle-line-endings) the global git setting - `core.autocrlf` (for Windows - must be equal to false) and after changing it, clone the repo again.


### System testing

#### Adjustable parameters

It is possible to regulate the **speed of "sensor polling"**. In the `docker-compose.yml` file for the `iot` service, it is possible to set the desired value as the last parameter (in this case, the speed is 30 seconds):
```
command: ["./wait-for-it.sh", "-t","240","middleware:4000", "--", "python", "client.py", "30"] 
```
This means that in one poll from IoT to Middleware 11 values are transferred (1 row from `apartment2016.xlsx`), then there is a delay of 30 seconds - and then a new poll.

The **number of blocks** for viewing previous data can also be adjusted. This is in the last parameter of the `user` service (in this case, it is 100 blocks):
```
command: ["./wait-for-it.sh", "-t","240","middleware:4001", "--", "python", "user.py", "100"]
```

#### Filter

Filtering parameters are stored on the Middleware side in the `IoT_thresholds.json` file. It is possible to set the **Low threshold** and **High threshold** values through the web interface in the appropriate fields for a specific "sensor".

The filter means:
- if both values are 0, then the filter is not applied
- if the filter is set, then only critical values will be added to the blockchain: less than the **Low threshold** value, or more than the **High threshold**

For example, the initial filter values are applied to four “sensors” (on the right), and as a result, only 281 will be written to the blockchain from the `windBearing` sensor (more than **High threshold**==280):

![Filter image](/Filtering.png)

After several polls, you can test the filter by refreshing the web page and writing the name of the "sensor" in the search field - the table will display data only for this "sensor". For example, `cloudCover` will only have three values: 0.75, 0.6, and 1.0.

Notes:
- Two text columns and a date column have been excluded from the table, so there are 11 "sensors" in total.
- For fields where there is no data, such as the "sensor" `cloudCover`, the value is set to 0 (in the case of writing to the blockchain).

#### Notifications

On the User side, a check for new records in the blockchain is performed every 30 seconds. As soon as they are found, a notification will appear at the top of the web interface containing the current date and time of new records being discovered, their number, and a link to open a separate page to view them.


## Docker
### Docker images
Images for the **IoT** (*natasha256/blockchain-iot*), **middleware** (*natasha256/blockchain-middleware*) and **user** (*natasha256/blockchain-user*) parts can be downloaded from [DockerHub](https://hub.docker.com/u/natasha256).

Tags:

- **3.0**: Containerized Stage 2 (Ropsten)
- **2.0**: Containerized Stage 2 (local, Ganache)
- **latest**: Containerized Stage 1

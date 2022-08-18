pragma solidity ^0.8.15;

contract IoT {
    address public contractOwner;
    string date;
    string param;
    uint32 value;
    
    event IotData(string d, string p, uint32 v);

    modifier onlyOwner {
        require(msg.sender == contractOwner, "Only owner can call this function.");
        _;
    }

    constructor() public {
        contractOwner = msg.sender;
    }

    function setData(string memory _date, string memory _param, uint32 _value) public onlyOwner {
        date = _date;
        param = _param;
        value = _value;
        emit IotData(_date, _param, _value);
    }

    function getData() view public returns (string memory, string memory, uint32) {
        return (date, param, value);
    }

}
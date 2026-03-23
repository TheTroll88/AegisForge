// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SignalRegistry {
    struct Signal {
        address creator;
        string command;
        uint256 timestamp;
    }

    Signal[] public signals;

    event SignalCreated(address indexed creator, string command, uint256 timestamp);

    function createSignal(string memory _command) public {
        Signal memory newSignal = Signal({
            creator: msg.sender,
            command: _command,
            timestamp: block.timestamp
        });

        signals.push(newSignal);
        emit SignalCreated(msg.sender, _command, block.timestamp);
    }
}

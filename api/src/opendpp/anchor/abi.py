"""Minimal ABI for the OpenDPPAnchor contract.

Hand-written rather than imported from the Hardhat artifact so the API
doesn't need to read from a build directory on startup. Kept in sync with
contracts/contracts/OpenDPPAnchor.sol.
"""

OPENDPP_ANCHOR_ABI = [
    {
        "type": "event",
        "name": "Anchored",
        "anonymous": False,
        "inputs": [
            {"name": "hash", "type": "bytes32", "indexed": True},
            {"name": "anchorer", "type": "address", "indexed": True},
            {"name": "timestamp", "type": "uint256", "indexed": False},
        ],
    },
    {
        "type": "function",
        "name": "anchor",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "hash", "type": "bytes32"}],
        "outputs": [],
    },
    {
        "type": "function",
        "name": "anchorBatch",
        "stateMutability": "nonpayable",
        "inputs": [{"name": "hashes", "type": "bytes32[]"}],
        "outputs": [],
    },
    {
        "type": "function",
        "name": "anchoredAt",
        "stateMutability": "view",
        "inputs": [{"name": "hash", "type": "bytes32"}],
        "outputs": [{"name": "", "type": "uint256"}],
    },
]

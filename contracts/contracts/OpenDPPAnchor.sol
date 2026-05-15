// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title OpenDPPAnchor
/// @notice Stores cryptographic hashes of Digital Product Passport snapshots
///         for public, OpenDPP-independent tamper-evidence.
/// @dev Anchoring is a one-shot per hash. Re-anchoring the same hash reverts.
///      `anchoredAt[hash]` returns 0 if the hash has never been anchored, or
///      the block timestamp at which it was first anchored.
///      The contract holds no per-product state — anyone can reproduce the
///      hash off-chain and query this contract directly to verify integrity.
contract OpenDPPAnchor {
    /// @notice Emitted on every successful anchor.
    /// @param hash The 32-byte snapshot hash.
    /// @param anchorer The address that submitted the anchor transaction.
    /// @param timestamp The block timestamp at which the anchor was recorded.
    event Anchored(bytes32 indexed hash, address indexed anchorer, uint256 timestamp);

    /// @notice Unix timestamp at which a given hash was first anchored.
    /// @dev Returns 0 if the hash has never been anchored.
    mapping(bytes32 => uint256) public anchoredAt;

    /// @notice Anchor a snapshot hash on-chain. Each hash can be anchored once.
    /// @param hash The 32-byte SHA-256 (or any 256-bit digest) of the DPP snapshot.
    function anchor(bytes32 hash) external {
        require(anchoredAt[hash] == 0, "OpenDPPAnchor: already anchored");
        anchoredAt[hash] = block.timestamp;
        emit Anchored(hash, msg.sender, block.timestamp);
    }

    /// @notice Batch-anchor multiple snapshot hashes in a single transaction.
    /// @param hashes The list of 32-byte digests to anchor. Reverts if any one
    ///        has already been anchored — caller should filter beforehand.
    function anchorBatch(bytes32[] calldata hashes) external {
        for (uint256 i = 0; i < hashes.length; i++) {
            bytes32 h = hashes[i];
            require(anchoredAt[h] == 0, "OpenDPPAnchor: already anchored");
            anchoredAt[h] = block.timestamp;
            emit Anchored(h, msg.sender, block.timestamp);
        }
    }
}

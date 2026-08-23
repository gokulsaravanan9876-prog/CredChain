// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title CredentialAnchor
/// @notice Stores an immutable, timestamped anchor for a credential hash.
///         This contract deliberately stores nothing about the credential
///         itself — no names, no documents, no personal data — only the
///         cryptographic hash CredChain already computes off-chain from its
///         existing canonical credential payload, plus who anchored it and
///         when. The hash is a one-way digest: it proves "this exact
///         credential data existed and was anchored by this issuer at this
///         time" without revealing what the data was.
contract CredentialAnchor {
    struct Anchor {
        address issuer;
        uint256 timestamp;
        bool exists;
    }

    /// credentialHash => anchor record.
    mapping(bytes32 => Anchor) private anchors;

    event CredentialAnchored(bytes32 indexed credentialHash, address indexed issuer, uint256 timestamp);

    error AlreadyAnchored(bytes32 credentialHash);

    /// @notice Anchors a credential hash on-chain. Reverts if this exact
    ///         hash has already been anchored — anchoring is write-once per
    ///         hash, never a silent overwrite, so an anchor timestamp can
    ///         always be trusted as the original anchoring time.
    function anchorCredential(bytes32 credentialHash) external {
        if (anchors[credentialHash].exists) {
            revert AlreadyAnchored(credentialHash);
        }
        anchors[credentialHash] = Anchor({issuer: msg.sender, timestamp: block.timestamp, exists: true});
        emit CredentialAnchored(credentialHash, msg.sender, block.timestamp);
    }

    /// @notice Reads back the anchor for a given credential hash.
    /// @return issuer The address that anchored this hash (address(0) if never anchored).
    /// @return timestamp The block timestamp the hash was anchored at (0 if never anchored).
    /// @return exists Whether this hash has been anchored at all.
    function getCredentialAnchor(bytes32 credentialHash)
        external
        view
        returns (address issuer, uint256 timestamp, bool exists)
    {
        Anchor storage anchor = anchors[credentialHash];
        return (anchor.issuer, anchor.timestamp, anchor.exists);
    }
}

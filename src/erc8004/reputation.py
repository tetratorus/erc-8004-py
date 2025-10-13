"""
Reputation Client for ERC-8004
Handles feedback submission and reputation queries
"""

import json
import os
from typing import Dict, List, Optional

from eth_abi import encode
from web3 import Web3

from .adapters.base import BlockchainAdapter
from .types import FeedbackAuth, Summary


class ReputationClient:
    """Client for interacting with the ERC-8004 Reputation Registry"""

    def __init__(
        self,
        adapter: BlockchainAdapter,
        contract_address: str,
        identity_registry_address: str,
    ):
        """
        Initialize Reputation Client

        Args:
            adapter: Blockchain adapter instance
            contract_address: Address of the Reputation Registry contract
            identity_registry_address: Address of the Identity Registry contract
        """
        self.adapter = adapter
        self.contract_address = contract_address
        self.identity_registry_address = identity_registry_address

        # Load ABI
        abi_path = os.path.join(
            os.path.dirname(__file__), "abis", "ReputationRegistry.json"
        )
        with open(abi_path, "r") as f:
            self.abi = json.load(f)

    def create_feedback_auth(
        self,
        agent_id: int,
        client_address: str,
        index_limit: int,
        expiry: int,
        chain_id: int,
        signer_address: str,
    ) -> FeedbackAuth:
        """
        Create a feedbackAuth structure to be signed
        Spec: tuple (agentId, clientAddress, indexLimit, expiry, chainId, identityRegistry, signerAddress)

        Args:
            agent_id: The agent ID
            client_address: Address authorized to give feedback
            index_limit: Must be > last feedback index from this client (typically lastIndex + 1)
            expiry: Unix timestamp when authorization expires
            chain_id: Chain ID where feedback will be submitted
            signer_address: Address of the signer (agent owner/operator)

        Returns:
            FeedbackAuth dictionary
        """
        return {
            "agentId": agent_id,
            "clientAddress": client_address,
            "indexLimit": index_limit,
            "expiry": expiry,
            "chainId": chain_id,
            "identityRegistry": self.identity_registry_address,
            "signerAddress": signer_address,
        }

    def sign_feedback_auth(self, auth: FeedbackAuth) -> str:
        """
        Sign a feedbackAuth using EIP-191
        The agent owner/operator signs to authorize a client to give feedback

        Args:
            auth: The feedbackAuth structure

        Returns:
            Signed authorization as bytes (encoded tuple + signature concatenated)
        """
        # Encode the feedbackAuth tuple
        # Spec: (agentId, clientAddress, indexLimit, expiry, chainId, identityRegistry, signerAddress)
        encoded = encode(
            ["uint256", "address", "uint256", "uint256", "uint256", "address", "address"],
            [
                auth["agentId"],
                Web3.to_checksum_address(auth["clientAddress"]),
                auth["indexLimit"],
                auth["expiry"],
                auth["chainId"],
                Web3.to_checksum_address(auth["identityRegistry"]),
                Web3.to_checksum_address(auth["signerAddress"]),
            ],
        )

        # Hash the encoded data
        message_hash = Web3.keccak(encoded)

        # Sign using EIP-191 (personal_sign)
        # This prefixes the message with "\x19Ethereum Signed Message:\n32"
        signature = self.adapter.sign_message(message_hash)

        # Return encoded tuple + signature concatenated
        # Remove '0x' prefix from signature if present
        sig_hex = signature[2:] if signature.startswith('0x') else signature
        return "0x" + encoded.hex() + sig_hex

    def give_feedback(
        self,
        agent_id: int,
        score: int,
        feedback_auth: str,
        tag1: Optional[str] = None,
        tag2: Optional[str] = None,
        fileuri: Optional[str] = None,
        filehash: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Submit feedback for an agent
        Spec: function giveFeedback(uint256 agentId, uint8 score, bytes32 tag1, bytes32 tag2, string calldata fileuri, bytes32 calldata filehash, bytes memory feedbackAuth)

        Args:
            agent_id: The agent ID
            score: Score 0-100 (MUST)
            feedback_auth: Signed feedbackAuth
            tag1: OPTIONAL tag (will be hashed to bytes32)
            tag2: OPTIONAL tag (will be hashed to bytes32)
            fileuri: OPTIONAL file URI
            filehash: OPTIONAL file hash (bytes32)

        Returns:
            Dictionary with txHash
        """
        # Validate score is 0-100 (MUST per spec)
        if score < 0 or score > 100:
            raise ValueError("Score MUST be between 0 and 100")

        # Convert optional string parameters to bytes32 (or empty bytes32 if not provided)
        tag1_bytes = Web3.keccak(text=tag1) if tag1 else bytes(32)
        tag2_bytes = Web3.keccak(text=tag2) if tag2 else bytes(32)
        filehash_bytes = bytes.fromhex(filehash[2:]) if filehash else bytes(32)
        fileuri_str = fileuri or ""

        result = self.adapter.send(
            self.contract_address,
            self.abi,
            "giveFeedback",
            [
                agent_id,
                score,
                tag1_bytes,
                tag2_bytes,
                fileuri_str,
                filehash_bytes,
                bytes.fromhex(feedback_auth[2:]),
            ],
        )

        return {"txHash": result["txHash"]}

    def revoke_feedback(self, agent_id: int, feedback_index: int) -> Dict[str, str]:
        """
        Revoke previously submitted feedback
        Spec: function revokeFeedback(uint256 agentId, uint64 feedbackIndex)

        Args:
            agent_id: The agent ID
            feedback_index: Index of feedback to revoke

        Returns:
            Dictionary with txHash
        """
        result = self.adapter.send(
            self.contract_address, self.abi, "revokeFeedback", [agent_id, feedback_index]
        )

        return {"txHash": result["txHash"]}

    def append_response(
        self,
        agent_id: int,
        client_address: str,
        feedback_index: int,
        response_uri: str,
        response_hash: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Append a response to existing feedback
        Spec: function appendResponse(uint256 agentId, address clientAddress, uint64 feedbackIndex, string calldata responseUri, bytes32 calldata responseHash)

        Args:
            agent_id: The agent ID
            client_address: Client who gave the feedback
            feedback_index: Index of the feedback
            response_uri: URI to response content
            response_hash: OPTIONAL hash of response content (KECCAK-256)

        Returns:
            Dictionary with txHash
        """
        hash_bytes = bytes.fromhex(response_hash[2:]) if response_hash else bytes(32)

        result = self.adapter.send(
            self.contract_address,
            self.abi,
            "appendResponse",
            [agent_id, client_address, feedback_index, response_uri, hash_bytes],
        )

        return {"txHash": result["txHash"]}

    def get_identity_registry(self) -> str:
        """
        Get the identity registry address
        Spec: function getIdentityRegistry() external view returns (address identityRegistry)

        Returns:
            Identity registry address
        """
        return self.adapter.call(
            self.contract_address, self.abi, "getIdentityRegistry", []
        )

    def get_summary(
        self,
        agent_id: int,
        client_addresses: Optional[List[str]] = None,
        tag1: Optional[str] = None,
        tag2: Optional[str] = None,
    ) -> Summary:
        """
        Get reputation summary for an agent
        Spec: function getSummary(uint256 agentId, address[] calldata clientAddresses, bytes32 tag1, bytes32 tag2) returns (uint64 count, uint8 averageScore)
        Note: agentId is ONLY mandatory parameter, others are OPTIONAL filters

        Args:
            agent_id: The agent ID (MANDATORY)
            client_addresses: OPTIONAL filter by specific clients
            tag1: OPTIONAL filter by tag1
            tag2: OPTIONAL filter by tag2

        Returns:
            Summary dictionary with count and averageScore
        """
        clients = client_addresses or []
        t1 = Web3.keccak(text=tag1) if tag1 else bytes(32)
        t2 = Web3.keccak(text=tag2) if tag2 else bytes(32)

        result = self.adapter.call(
            self.contract_address, self.abi, "getSummary", [agent_id, clients, t1, t2]
        )

        return {"count": int(result[0]), "averageScore": int(result[1])}

    def read_feedback(
        self, agent_id: int, client_address: str, index: int
    ) -> Dict[str, any]:
        """
        Read a specific feedback entry
        Spec: function readFeedback(uint256 agentId, address clientAddress, uint64 index) returns (uint8 score, bytes32 tag1, bytes32 tag2, bool isRevoked)

        Args:
            agent_id: The agent ID
            client_address: Client who gave feedback
            index: Feedback index

        Returns:
            Dictionary with score, tag1, tag2, isRevoked
        """
        result = self.adapter.call(
            self.contract_address,
            self.abi,
            "readFeedback",
            [agent_id, client_address, index],
        )

        return {
            "score": int(result[0]),
            "tag1": result[1].hex() if isinstance(result[1], bytes) else result[1],
            "tag2": result[2].hex() if isinstance(result[2], bytes) else result[2],
            "isRevoked": bool(result[3]),
        }

    def read_all_feedback(
        self,
        agent_id: int,
        client_addresses: Optional[List[str]] = None,
        tag1: Optional[str] = None,
        tag2: Optional[str] = None,
        include_revoked: bool = False,
    ) -> Dict[str, List]:
        """
        Read all feedback for an agent with optional filters
        Spec: function readAllFeedback(uint256 agentId, address[] calldata clientAddresses, bytes32 tag1, bytes32 tag2, bool includeRevoked) returns arrays
        Note: agentId is ONLY mandatory parameter

        Args:
            agent_id: The agent ID (MANDATORY)
            client_addresses: OPTIONAL filter by clients
            tag1: OPTIONAL filter by tag1
            tag2: OPTIONAL filter by tag2
            include_revoked: OPTIONAL include revoked feedback

        Returns:
            Dictionary with arrays of clientAddresses, scores, tag1s, tag2s, revokedStatuses
        """
        clients = client_addresses or []
        t1 = Web3.keccak(text=tag1) if tag1 else bytes(32)
        t2 = Web3.keccak(text=tag2) if tag2 else bytes(32)

        result = self.adapter.call(
            self.contract_address,
            self.abi,
            "readAllFeedback",
            [agent_id, clients, t1, t2, include_revoked],
        )

        return {
            "clientAddresses": list(result[0]),
            "scores": [int(s) for s in result[1]],
            "tag1s": [t.hex() if isinstance(t, bytes) else t for t in result[2]],
            "tag2s": [t.hex() if isinstance(t, bytes) else t for t in result[3]],
            "revokedStatuses": [bool(r) for r in result[4]],
        }

    def get_response_count(
        self,
        agent_id: int,
        client_address: Optional[str] = None,
        feedback_index: Optional[int] = None,
        responders: Optional[List[str]] = None,
    ) -> int:
        """
        Get response count for a feedback entry
        Spec: function getResponseCount(uint256 agentId, address clientAddress, uint64 feedbackIndex, address[] responders) returns (uint64)
        Note: agentId is ONLY mandatory parameter

        Args:
            agent_id: The agent ID (MANDATORY)
            client_address: OPTIONAL client address
            feedback_index: OPTIONAL feedback index
            responders: OPTIONAL responder addresses

        Returns:
            Response count
        """
        client = client_address or "0x0000000000000000000000000000000000000000"
        index = feedback_index or 0
        resp = responders or []

        result = self.adapter.call(
            self.contract_address,
            self.abi,
            "getResponseCount",
            [agent_id, client, index, resp],
        )

        return int(result)

    def get_clients(self, agent_id: int) -> List[str]:
        """
        Get all clients who have given feedback to an agent
        Spec: function getClients(uint256 agentId) returns (address[] memory)

        Args:
            agent_id: The agent ID

        Returns:
            List of client addresses
        """
        return self.adapter.call(self.contract_address, self.abi, "getClients", [agent_id])

    def get_last_index(self, agent_id: int, client_address: str) -> int:
        """
        Get the last feedback index from a client for an agent
        Spec: function getLastIndex(uint256 agentId, address clientAddress) returns (uint64)

        Args:
            agent_id: The agent ID
            client_address: Client address

        Returns:
            Last feedback index (0 if no feedback yet)
        """
        result = self.adapter.call(
            self.contract_address, self.abi, "getLastIndex", [agent_id, client_address]
        )

        return int(result)

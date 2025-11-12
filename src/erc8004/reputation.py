"""
Reputation Client for ERC-8004
Handles feedback submission and reputation queries
"""

import json
import os
from typing import Dict, List, Optional

from .adapters.base import BlockchainAdapter
from .types import Summary


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


    def give_feedback(
        self,
        agent_id: int,
        score: int,
        tag1: Optional[str] = None,
        tag2: Optional[str] = None,
        feedback_uri: Optional[str] = None,
        feedback_hash: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Submit feedback for an agent
        Spec: function giveFeedback(uint256 agentId, uint8 score, string tag1, string tag2, string calldata feedbackUri, bytes32 calldata feedbackHash)
        NOTE: feedbackAuth has been REMOVED in the new contract

        Args:
            agent_id: The agent ID
            score: Score 0-100 (MUST)
            tag1: OPTIONAL tag (now a string, not bytes32)
            tag2: OPTIONAL tag (now a string, not bytes32)
            feedback_uri: OPTIONAL feedback URI
            feedback_hash: OPTIONAL feedback hash (bytes32)

        Returns:
            Dictionary with txHash
        """
        # Validate score is 0-100 (MUST per spec)
        if score < 0 or score > 100:
            raise ValueError("Score MUST be between 0 and 100")

        # NEW: Tags are now strings, pass them directly
        tag1_str = tag1 or ""
        tag2_str = tag2 or ""
        feedback_hash_bytes = bytes.fromhex(feedback_hash[2:]) if feedback_hash else bytes(32)
        feedback_uri_str = feedback_uri or ""

        result = self.adapter.send(
            self.contract_address,
            self.abi,
            "giveFeedback",
            [
                agent_id,
                score,
                tag1_str,
                tag2_str,
                feedback_uri_str,
                feedback_hash_bytes,
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
        Spec: function getSummary(uint256 agentId, address[] calldata clientAddresses, string tag1, string tag2) returns (uint64 count, uint8 averageScore)
        Note: agentId is ONLY mandatory parameter, others are OPTIONAL filters

        Args:
            agent_id: The agent ID (MANDATORY)
            client_addresses: OPTIONAL filter by specific clients
            tag1: OPTIONAL filter by tag1 (now a string, not bytes32)
            tag2: OPTIONAL filter by tag2 (now a string, not bytes32)

        Returns:
            Summary dictionary with count and averageScore
        """
        clients = client_addresses or []
        # NEW: Tags are now strings, pass them directly
        t1 = tag1 or ""
        t2 = tag2 or ""

        result = self.adapter.call(
            self.contract_address, self.abi, "getSummary", [agent_id, clients, t1, t2]
        )

        return {"count": int(result[0]), "averageScore": int(result[1])}

    def read_feedback(
        self, agent_id: int, client_address: str, index: int
    ) -> Dict[str, any]:
        """
        Read a specific feedback entry
        Spec: function readFeedback(uint256 agentId, address clientAddress, uint64 index) returns (uint8 score, string tag1, string tag2, bool isRevoked)

        Args:
            agent_id: The agent ID
            client_address: Client who gave feedback
            index: Feedback index

        Returns:
            Dictionary with score, tag1, tag2, isRevoked (tags are now strings)
        """
        result = self.adapter.call(
            self.contract_address,
            self.abi,
            "readFeedback",
            [agent_id, client_address, index],
        )

        # NEW: Tags are now strings, no hex conversion needed
        return {
            "score": int(result[0]),
            "tag1": result[1],
            "tag2": result[2],
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
        Spec: function readAllFeedback(uint256 agentId, address[] calldata clientAddresses, string tag1, string tag2, bool includeRevoked) returns arrays
        Note: agentId is ONLY mandatory parameter

        Args:
            agent_id: The agent ID (MANDATORY)
            client_addresses: OPTIONAL filter by clients
            tag1: OPTIONAL filter by tag1 (now a string, not bytes32)
            tag2: OPTIONAL filter by tag2 (now a string, not bytes32)
            include_revoked: OPTIONAL include revoked feedback

        Returns:
            Dictionary with arrays of clientAddresses, scores, tag1s, tag2s, revokedStatuses (tags are now strings)
        """
        clients = client_addresses or []
        # NEW: Tags are now strings, pass them directly
        t1 = tag1 or ""
        t2 = tag2 or ""

        result = self.adapter.call(
            self.contract_address,
            self.abi,
            "readAllFeedback",
            [agent_id, clients, t1, t2, include_revoked],
        )

        # NEW: Tags are now strings, no hex conversion needed
        return {
            "clientAddresses": list(result[0]),
            "scores": [int(s) for s in result[1]],
            "tag1s": list(result[2]),
            "tag2s": list(result[3]),
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

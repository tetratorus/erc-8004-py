"""
Identity Client for ERC-8004
Handles agent registration and identity management
"""

import json
import os
from typing import Dict, List, Optional

import requests

from .adapters.base import BlockchainAdapter
from .types import AgentRegistrationFile, MetadataEntry


class IdentityClient:
    """Client for interacting with the ERC-8004 Identity Registry"""

    def __init__(self, adapter: BlockchainAdapter, contract_address: str):
        """
        Initialize Identity Client

        Args:
            adapter: Blockchain adapter instance
            contract_address: Address of the Identity Registry contract
        """
        self.adapter = adapter
        self.contract_address = contract_address

        # Load ABI
        abi_path = os.path.join(
            os.path.dirname(__file__), "abis", "IdentityRegistry.json"
        )
        with open(abi_path, "r") as f:
            self.abi = json.load(f)

    def register(self) -> Dict[str, any]:
        """
        Register a new agent with no URI (URI can be set later)
        Spec: function register() returns (uint256 agentId)

        Returns:
            Dictionary with agentId and txHash
        """
        result = self.adapter.send(
            self.contract_address, self.abi, "register", []
        )

        # Extract agentId from receipt
        agent_id = self._extract_agent_id_from_receipt(result)

        return {"agentId": agent_id, "txHash": result["txHash"]}

    def register_with_uri(self, token_uri: str) -> Dict[str, any]:
        """
        Register a new agent with a token URI
        Spec: function register(string tokenURI) returns (uint256 agentId)

        Args:
            token_uri: URI pointing to agent registration file (MAY use ipfs://, https://, etc.)

        Returns:
            Dictionary with agentId and txHash
        """
        result = self.adapter.send(
            self.contract_address, self.abi, "register", [token_uri]
        )

        agent_id = self._extract_agent_id_from_receipt(result)

        return {"agentId": agent_id, "txHash": result["txHash"]}

    def register_with_metadata(
        self, token_uri: str, metadata: Optional[List[MetadataEntry]] = None
    ) -> Dict[str, any]:
        """
        Register a new agent with URI and optional on-chain metadata
        Spec: function register(string tokenURI, MetadataEntry[] calldata metadata) returns (uint256 agentId)

        Args:
            token_uri: URI pointing to agent registration file
            metadata: OPTIONAL on-chain metadata entries

        Returns:
            Dictionary with agentId and txHash
        """
        if metadata is None:
            metadata = []

        # Convert metadata to contract format
        metadata_formatted = [
            {"key": m["key"], "value": m["value"].encode("utf-8")} for m in metadata
        ]

        result = self.adapter.send(
            self.contract_address, self.abi, "register", [token_uri, metadata_formatted]
        )

        agent_id = self._extract_agent_id_from_receipt(result)

        return {"agentId": agent_id, "txHash": result["txHash"]}

    def get_token_uri(self, agent_id: int) -> str:
        """
        Get the token URI for an agent
        Spec: Standard ERC-721 tokenURI function

        Args:
            agent_id: The agent's ID

        Returns:
            URI string (MAY be ipfs://, https://, etc.)
        """
        return self.adapter.call(self.contract_address, self.abi, "tokenURI", [agent_id])

    def set_agent_uri(self, agent_id: int, new_uri: str) -> Dict[str, str]:
        """
        Set the token URI for an agent
        Note: This is an implementation-specific extension (not in base spec).
        Assumes implementation exposes setAgentUri with owner/operator checks.

        Args:
            agent_id: The agent's ID
            new_uri: New URI string

        Returns:
            Dictionary with txHash
        """
        result = self.adapter.send(
            self.contract_address, self.abi, "setAgentUri", [agent_id, new_uri]
        )

        return {"txHash": result["txHash"]}

    def get_owner(self, agent_id: int) -> str:
        """
        Get the owner of an agent
        Spec: Standard ERC-721 ownerOf function

        Args:
            agent_id: The agent's ID

        Returns:
            Owner address
        """
        return self.adapter.call(self.contract_address, self.abi, "ownerOf", [agent_id])

    def get_metadata(self, agent_id: int, key: str) -> str:
        """
        Get on-chain metadata for an agent
        Spec: function getMetadata(uint256 agentId, string key) returns (bytes)

        Args:
            agent_id: The agent's ID
            key: Metadata key

        Returns:
            Metadata value as string
        """
        bytes_value = self.adapter.call(
            self.contract_address, self.abi, "getMetadata", [agent_id, key]
        )
        return self._bytes_to_string(bytes_value)

    def set_metadata(self, agent_id: int, key: str, value: str) -> Dict[str, str]:
        """
        Set on-chain metadata for an agent
        Spec: function setMetadata(uint256 agentId, string key, bytes value)

        Args:
            agent_id: The agent's ID
            key: Metadata key
            value: Metadata value

        Returns:
            Dictionary with txHash
        """
        result = self.adapter.send(
            self.contract_address,
            self.abi,
            "setMetadata",
            [agent_id, key, value.encode("utf-8")],
        )

        return {"txHash": result["txHash"]}

    def get_registration_file(self, agent_id: int) -> AgentRegistrationFile:
        """
        Fetch and parse the agent registration file from the token URI
        This is a convenience function that fetches the URI and parses it
        Note: Does not validate - spec says ERC-8004 cannot cryptographically guarantee
        that advertised capabilities are functional

        Args:
            agent_id: The agent's ID

        Returns:
            Parsed agent registration file
        """
        uri = self.get_token_uri(agent_id)

        # Handle different URI schemes
        if uri.startswith("ipfs://"):
            # IPFS gateway - using public gateway
            cid = uri.replace("ipfs://", "")
            http_uri = f"https://ipfs.io/ipfs/{cid}"
            response = requests.get(http_uri)
            response.raise_for_status()
            return response.json()
        elif uri.startswith("https://") or uri.startswith("http://"):
            response = requests.get(uri)
            response.raise_for_status()
            return response.json()
        else:
            raise ValueError(f"Unsupported URI scheme: {uri}")

    def _extract_agent_id_from_receipt(self, result: Dict) -> int:
        """
        Helper: Extract agentId from transaction receipt
        Looks for the Registered event which contains the agentId
        """
        if "events" in result:
            for event in result["events"]:
                if event["name"] == "Registered":
                    args = event["args"]
                    return int(args.get("agentId", args.get(0)))

        raise ValueError(
            "Could not extract agentId from transaction receipt - Registered event not found"
        )

    def _bytes_to_string(self, bytes_value: any) -> str:
        """Helper: Convert bytes to string (adapter-agnostic)"""
        if isinstance(bytes_value, bytes):
            return bytes_value.decode("utf-8")
        elif isinstance(bytes_value, str) and bytes_value.startswith("0x"):
            # Hex string format
            hex_str = bytes_value[2:]
            byte_array = bytes.fromhex(hex_str)
            return byte_array.decode("utf-8")
        return str(bytes_value)

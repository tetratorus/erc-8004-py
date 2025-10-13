"""
Validation Client for ERC-8004
Handles validation requests and responses
"""

import json
import os
from typing import Dict, List, Optional

from web3 import Web3

from .adapters.base import BlockchainAdapter
from .types import ValidationStatus


class ValidationClient:
    """Client for interacting with the ERC-8004 Validation Registry"""

    def __init__(self, adapter: BlockchainAdapter, contract_address: str):
        """
        Initialize Validation Client

        Args:
            adapter: Blockchain adapter instance
            contract_address: Address of the Validation Registry contract
        """
        self.adapter = adapter
        self.contract_address = contract_address

        # Load ABI
        abi_path = os.path.join(
            os.path.dirname(__file__), "abis", "ValidationRegistry.json"
        )
        with open(abi_path, "r") as f:
            self.abi = json.load(f)

    def validation_request(
        self,
        validator_address: str,
        agent_id: int,
        request_uri: str,
        request_hash: str,
    ) -> Dict[str, str]:
        """
        Request validation from a validator
        Spec: function validationRequest(address validatorAddress, uint256 agentId, string requestUri, bytes32 requestHash)
        Note: MUST be called by owner or operator of agentId
        Note: requestHash MUST be keccak256 of the content at requestUri

        Args:
            validator_address: Validator address (MANDATORY)
            agent_id: Agent ID (MANDATORY)
            request_uri: URI to validation request content (MANDATORY)
            request_hash: Hash of content at requestUri (MANDATORY, bytes32)

        Returns:
            Dictionary with txHash and requestHash
        """
        result = self.adapter.send(
            self.contract_address,
            self.abi,
            "validationRequest",
            [validator_address, agent_id, request_uri, request_hash],
        )

        return {"txHash": result["txHash"], "requestHash": request_hash}

    def validation_response(
        self,
        request_hash: str,
        response: int,
        response_uri: Optional[str] = None,
        response_hash: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Provide a validation response
        Spec: function validationResponse(bytes32 requestHash, uint8 response, string responseUri, bytes32 responseHash, bytes32 tag)
        Note: MUST be called by the validatorAddress specified in the original request
        Note: Can be called multiple times for the same requestHash

        Args:
            request_hash: Request hash (MANDATORY, bytes32)
            response: Response value 0-100 (MANDATORY)
            response_uri: URI to response content (OPTIONAL)
            response_hash: Hash of response content (OPTIONAL, bytes32)
            tag: Tag for categorization (OPTIONAL, bytes32)

        Returns:
            Dictionary with txHash
        """
        # Validate response is 0-100
        if response < 0 or response > 100:
            raise ValueError("Response MUST be between 0 and 100")

        # Convert optional parameters to proper format
        response_uri_str = response_uri or ""
        response_hash_bytes = (
            bytes.fromhex(response_hash[2:]) if response_hash else bytes(32)
        )
        tag_bytes = Web3.keccak(text=tag) if tag else bytes(32)

        result = self.adapter.send(
            self.contract_address,
            self.abi,
            "validationResponse",
            [request_hash, response, response_uri_str, response_hash_bytes, tag_bytes],
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

    def get_validation_status(self, request_hash: str) -> ValidationStatus:
        """
        Get validation status for a request
        Spec: function getValidationStatus(bytes32 requestHash) returns (address validatorAddress, uint256 agentId, uint8 response, bytes32 tag, uint256 lastUpdate)

        Args:
            request_hash: The request hash (bytes32)

        Returns:
            ValidationStatus dictionary
        """
        result = self.adapter.call(
            self.contract_address, self.abi, "getValidationStatus", [request_hash]
        )

        return {
            "validatorAddress": result[0],
            "agentId": int(result[1]),
            "response": int(result[2]),
            "tag": result[3].hex() if isinstance(result[3], bytes) else result[3],
            "lastUpdate": int(result[4]),
        }

    def get_summary(
        self,
        agent_id: int,
        validator_addresses: Optional[List[str]] = None,
        tag: Optional[str] = None,
    ) -> Dict[str, any]:
        """
        Get validation summary for an agent
        Spec: function getSummary(uint256 agentId, address[] validatorAddresses, bytes32 tag) returns (uint64 count, uint8 avgResponse)
        Note: agentId is ONLY mandatory parameter, validatorAddresses and tag are OPTIONAL filters

        Args:
            agent_id: The agent ID (MANDATORY)
            validator_addresses: OPTIONAL filter by specific validators
            tag: OPTIONAL filter by tag

        Returns:
            Dictionary with count and avgResponse
        """
        validators = validator_addresses or []
        tag_bytes = Web3.keccak(text=tag) if tag else bytes(32)

        result = self.adapter.call(
            self.contract_address,
            self.abi,
            "getSummary",
            [agent_id, validators, tag_bytes],
        )

        return {"count": int(result[0]), "avgResponse": int(result[1])}

    def get_agent_validations(self, agent_id: int) -> List[str]:
        """
        Get all validation request hashes for an agent
        Spec: function getAgentValidations(uint256 agentId) returns (bytes32[] requestHashes)

        Args:
            agent_id: The agent ID

        Returns:
            List of request hashes
        """
        result = self.adapter.call(
            self.contract_address, self.abi, "getAgentValidations", [agent_id]
        )

        return [r.hex() if isinstance(r, bytes) else r for r in result]

    def get_validator_requests(self, validator_address: str) -> List[str]:
        """
        Get all request hashes for a validator
        Spec: function getValidatorRequests(address validatorAddress) returns (bytes32[] requestHashes)

        Args:
            validator_address: The validator address

        Returns:
            List of request hashes
        """
        result = self.adapter.call(
            self.contract_address, self.abi, "getValidatorRequests", [validator_address]
        )

        return [r.hex() if isinstance(r, bytes) else r for r in result]

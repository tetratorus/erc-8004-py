"""
Adapter interface for blockchain interactions
Allows SDK to work with any blockchain library (Web3.py, etc.)
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BlockchainAdapter(ABC):
    """
    Generic blockchain adapter interface
    Implementations provide library-specific functionality
    """

    @abstractmethod
    def call(
        self,
        contract_address: str,
        abi: List[Dict[str, Any]],
        function_name: str,
        args: List[Any],
    ) -> Any:
        """
        Call a read-only contract function

        Args:
            contract_address: Contract address
            abi: Contract ABI
            function_name: Function name to call
            args: Function arguments

        Returns:
            Function return value
        """
        pass

    @abstractmethod
    def send(
        self,
        contract_address: str,
        abi: List[Dict[str, Any]],
        function_name: str,
        args: List[Any],
    ) -> Dict[str, Any]:
        """
        Send a transaction to a contract function

        Args:
            contract_address: Contract address
            abi: Contract ABI
            function_name: Function name to call
            args: Function arguments

        Returns:
            Transaction result with txHash, blockNumber, events, etc.
        """
        pass

    @abstractmethod
    def get_address(self) -> Optional[str]:
        """
        Get the current signer/wallet address
        Returns None if no signer configured (read-only mode)

        Returns:
            Signer address or None
        """
        pass

    @abstractmethod
    def get_chain_id(self) -> int:
        """
        Get the chain ID

        Returns:
            Chain ID
        """
        pass

    @abstractmethod
    def sign_message(self, message: bytes) -> str:
        """
        Sign a message (EIP-191)

        Args:
            message: Message bytes to sign

        Returns:
            Signature as hex string
        """
        pass

    @abstractmethod
    def sign_typed_data(self, domain: Dict[str, Any], types: Dict[str, Any], value: Dict[str, Any]) -> str:
        """
        Sign typed data (EIP-712)

        Args:
            domain: EIP-712 domain
            types: EIP-712 types
            value: Message value

        Returns:
            Signature as hex string
        """
        pass

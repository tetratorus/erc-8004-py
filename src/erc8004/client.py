"""
ERC-8004 Trustless Agents Client

This SDK makes ZERO assumptions about implementations beyond what the spec says.
All "MAY" fields in the spec are treated as optional, not mandatory.

Uses adapter pattern to support any blockchain library (Web3.py, etc.)

Usage example:
```python
from erc8004 import ERC8004Client, Web3Adapter
from web3 import Web3

w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
adapter = Web3Adapter(w3, private_key='0x...')

client = ERC8004Client(
    adapter=adapter,
    addresses={
        'identityRegistry': '0x...',
        'reputationRegistry': '0x...',
        'validationRegistry': '0x...',
        'chainId': 31337
    }
)
```
"""

from typing import Dict, Optional

from .adapters.base import BlockchainAdapter
from .identity import IdentityClient
from .reputation import ReputationClient
from .types import ContractAddresses
from .validation import ValidationClient


class ERC8004Client:
    """Main client for interacting with ERC-8004 protocol"""

    def __init__(self, adapter: BlockchainAdapter, addresses: ContractAddresses):
        """
        Initialize ERC-8004 Client

        Args:
            adapter: Blockchain adapter instance (Web3Adapter, etc.)
            addresses: Contract addresses configuration
        """
        self.adapter = adapter
        self.addresses = addresses

        # Initialize sub-clients
        self.identity = IdentityClient(
            self.adapter, self.addresses["identityRegistry"]
        )

        self.reputation = ReputationClient(
            self.adapter,
            self.addresses["reputationRegistry"],
            self.addresses["identityRegistry"],
        )

        self.validation = ValidationClient(
            self.adapter, self.addresses["validationRegistry"]
        )

    def get_address(self) -> Optional[str]:
        """
        Get the current signer/wallet address
        Returns None if no signer configured (read-only mode)

        Returns:
            Signer address or None
        """
        return self.adapter.get_address()

    def get_chain_id(self) -> int:
        """
        Get the chain ID

        Returns:
            Chain ID
        """
        return self.adapter.get_chain_id()

    def get_addresses(self) -> Dict[str, any]:
        """
        Get the configured contract addresses

        Returns:
            Copy of addresses configuration
        """
        return dict(self.addresses)

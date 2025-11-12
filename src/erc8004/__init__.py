"""
ERC-8004 Trustless Agents SDK

A Python SDK for interacting with ERC-8004 compliant implementations.
Makes zero assumptions beyond what the spec says.
All "MAY" fields are optional, not mandatory.

Uses adapter pattern to support any blockchain library.
"""

from .adapters import BlockchainAdapter, Web3Adapter
from .client import ERC8004Client
from .identity import IdentityClient
from .reputation import ReputationClient
from .types import (
    AgentRegistrationFile,
    ContractAddresses,
    ERC8004Config,
    Feedback,
    FeedbackFile,
    MetadataEntry,
    Summary,
    ValidationStatus,
)
from .utils.ipfs import (
    IPFSClient,
    IPFSClientConfig,
    IPFSUploadResult,
    cid_to_bytes32,
    create_ipfs_client,
    ipfs_uri_to_bytes32,
)
from .validation import ValidationClient

__version__ = "0.1.0"

__all__ = [
    # Main client
    "ERC8004Client",
    # Sub-clients
    "IdentityClient",
    "ReputationClient",
    "ValidationClient",
    # Adapters
    "BlockchainAdapter",
    "Web3Adapter",
    # Types
    "AgentRegistrationFile",
    "ContractAddresses",
    "ERC8004Config",
    "Feedback",
    "FeedbackFile",
    "MetadataEntry",
    "Summary",
    "ValidationStatus",
    # IPFS utilities
    "IPFSClient",
    "IPFSClientConfig",
    "IPFSUploadResult",
    "cid_to_bytes32",
    "ipfs_uri_to_bytes32",
    "create_ipfs_client",
]

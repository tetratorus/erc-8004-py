"""
ERC-8004 SDK Types
All types strictly follow the ERC-8004 specification
"""

from typing import Any, Dict, List, Optional, TypedDict, Union
from typing_extensions import NotRequired


class MetadataEntry(TypedDict):
    """
    Metadata entry for agent registration
    Used when registering an agent with on-chain metadata
    """

    key: str
    value: str  # Will be converted to bytes in the contract


class Endpoint(TypedDict):
    """Agent endpoint definition"""

    name: str
    endpoint: str
    version: NotRequired[str]  # SHOULD but not MUST
    capabilities: NotRequired[Any]  # OPTIONAL, as per MCP spec


class Registration(TypedDict):
    """Agent registration entry"""

    agentId: int
    agentRegistry: str


class AgentRegistrationFile(TypedDict):
    """
    Agent registration file structure
    Fields marked OPTIONAL follow "MAY" requirements in the spec
    """

    type: str  # MUST be "https://eips.ethereum.org/EIPS/eip-8004#registration-v1"
    name: str  # MUST
    description: str  # MUST
    image: str  # MUST
    endpoints: NotRequired[List[Endpoint]]  # OPTIONAL
    registrations: NotRequired[List[Registration]]  # SHOULD have at least one
    supportedTrust: NotRequired[
        List[str]
    ]  # OPTIONAL: 'reputation' | 'crypto-economic' | 'tee-attestation'


class Feedback(TypedDict):
    """Feedback structure as stored on-chain"""

    score: int  # 0-100, MUST
    tag1: NotRequired[str]  # OPTIONAL (bytes32)
    tag2: NotRequired[str]  # OPTIONAL (bytes32)
    isRevoked: bool


class ProofOfPayment(TypedDict):
    """Proof of payment structure for x402"""

    fromAddress: str
    toAddress: str
    chainId: str
    txHash: str


class FeedbackFile(TypedDict):
    """
    Off-chain feedback file structure
    Fields beyond the MUST fields are all OPTIONAL per spec
    NOTE: feedbackAuth has been REMOVED in the new contract version
    """

    # MUST fields
    agentRegistry: str
    agentId: int
    clientAddress: str
    createdAt: str  # ISO 8601
    score: int

    # MAY fields (all optional)
    tag1: NotRequired[str]
    tag2: NotRequired[str]
    skill: NotRequired[str]
    context: NotRequired[str]
    task: NotRequired[str]
    capability: NotRequired[str]  # 'prompts' | 'resources' | 'tools' | 'completions'
    name: NotRequired[str]
    proof_of_payment: NotRequired[ProofOfPayment]


class Summary(TypedDict):
    """Summary statistics for reputation or validation"""

    count: int
    averageScore: int


class ValidationStatus(TypedDict):
    """Validation status"""

    validatorAddress: str
    agentId: int
    response: int  # 0-100
    responseHash: str  # bytes32 (may be empty/zero for older deployments)
    tag: str  # bytes32 (may be empty/zero)
    lastUpdate: int


class ContractAddresses(TypedDict):
    """Contract addresses configuration"""

    identityRegistry: str
    reputationRegistry: str
    validationRegistry: str
    chainId: int


class ERC8004Config(TypedDict):
    """SDK Configuration"""

    adapter: Any  # BlockchainAdapter instance
    addresses: ContractAddresses


class ContractCallResult(TypedDict):
    """Result from a contract transaction"""

    txHash: str
    blockNumber: NotRequired[int]

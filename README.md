# ERC-8004 SDK (Python)

Python SDK for interacting with ERC-8004 Trustless Agents protocol.

## Overview

ERC-8004 enables trustless agent economies through three core registries:

- **Identity Registry** - On-chain agent registration with portable identifiers
- **Reputation Registry** - Feedback and reputation scoring system
- **Validation Registry** - Independent validation and verification hooks

This SDK provides a simple, type-safe interface to interact with ERC-8004 contracts using **Web3.py**.

## Installation

```bash
pip install erc-8004-py
```

Or install from source:

```bash
git clone https://github.com/tetratorus/sdk
cd erc-8004-py
pip install -e .
```

## Quick Start

### Using Web3.py

```python
from erc8004 import ERC8004Client, Web3Adapter
from web3 import Web3

# Connect to Ethereum node
w3 = Web3(Web3.HTTPProvider('YOUR_RPC_URL'))

# Create adapter with private key
adapter = Web3Adapter(w3, private_key='0x...')

# Initialize client
client = ERC8004Client(
    adapter=adapter,
    addresses={
        'identityRegistry': '0x...',
        'reputationRegistry': '0x...',
        'validationRegistry': '0x...',
        'chainId': 11155111,  # Sepolia
    }
)

# Register an agent
result = client.identity.register_with_uri('ipfs://QmYourAgentData')
print(f"Agent ID: {result['agentId']}")
```

## Contract Addresses

### Sepolia (ChaosChainsAI Deployment)

```python
addresses = {
    'identityRegistry': '0x7177a6867296406881E20d6647232314736Dd09A',
    'reputationRegistry': '0xB5048e3ef1DA4E04deB6f7d0423D06F63869e322',
    'validationRegistry': '0x662b40A526cb4017d947e71eAF6753BF3eeE66d8',
    'chainId': 11155111,
}
```

## Core Features

### Identity Management

```python
# Register an agent
result = client.identity.register_with_uri('https://example.com/agent.json')
agent_id = result['agentId']

# Get agent info
owner = client.identity.get_owner(agent_id)
token_uri = client.identity.get_token_uri(agent_id)
```

### Reputation & Feedback

```python
import time

# Create feedback authorization (agent owner signs)
feedback_auth = client.reputation.create_feedback_auth(
    agent_id,
    client_address,
    index_limit,
    int(time.time()) + 3600,  # expiry
    chain_id,
    signer_address
)

signed_auth = client.reputation.sign_feedback_auth(feedback_auth)

# Submit feedback (client submits with signed auth)
client.reputation.give_feedback(
    agent_id=agent_id,
    score=95,  # 0-100
    tag1='excellent-service',
    tag2='fast-response',
    fileuri='ipfs://QmFeedbackData',
    feedback_auth=signed_auth,
)

# Get reputation summary
summary = client.reputation.get_summary(agent_id)
print(f"Average Score: {summary['averageScore']}")
print(f"Total Feedback: {summary['count']}")
```

### Validation

```python
from erc8004 import ipfs_uri_to_bytes32

# Request validation
request_uri = 'ipfs://QmValidationRequest'
request_hash = ipfs_uri_to_bytes32(request_uri)

client.validation.validation_request(
    validator_address=validator_address,
    agent_id=agent_id,
    request_uri=request_uri,
    request_hash=request_hash,
)

# Validator provides response
client.validation.validation_response(
    request_hash=request_hash,
    response=100,  # 0-100 (0=failed, 100=passed)
    response_uri='ipfs://QmValidationResponse',
    tag='zkML-proof',
)

# Read validation status
status = client.validation.get_validation_status(request_hash)
```

## IPFS Integration

The SDK includes comprehensive IPFS support for uploading, pinning, and fetching content.

### Quick Example

```python
from erc8004 import IPFSClientConfig, create_ipfs_client

# Create IPFS client (supports Pinata, NFT.Storage, Web3.Storage, local IPFS)
config = IPFSClientConfig(
    provider='pinata',
    api_key='YOUR_PINATA_API_KEY',
    api_secret='YOUR_PINATA_API_SECRET',
)
ipfs = create_ipfs_client(config)

# Upload agent registration data
agent_data = {
    'type': 'https://eips.ethereum.org/EIPS/eip-8004#registration-v1',
    'name': 'My Agent',
    'description': 'AI agent for task automation',
    'endpoints': [],  # Add your endpoints here
}

result = ipfs.upload_json(agent_data)
print(f"IPFS URI: {result.uri}")  # ipfs://Qm...

# Register agent with IPFS URI
client.identity.register_with_uri(result.uri)

# Fetch content from IPFS
data = ipfs.fetch_json(result.cid)
```

### CID Conversion Utilities

Convert IPFS CIDs to bytes32 for on-chain storage:

```python
from erc8004 import cid_to_bytes32, ipfs_uri_to_bytes32

# Convert CID to bytes32 for use as request hash
cid = 'QmR7GSQM93Cx5eAg6a6yRzNde1FQv7uL6X1o4k7zrJa3LX'
hash_bytes = cid_to_bytes32(cid)

# Or with ipfs:// URI
uri = 'ipfs://QmR7GSQM93Cx5eAg6a6yRzNde1FQv7uL6X1o4k7zrJa3LX'
hash_bytes2 = ipfs_uri_to_bytes32(uri)
```

📚 **[Full IPFS Guide](./docs/IPFS_GUIDE.md)** - Comprehensive documentation with examples for all IPFS providers

## Examples

See the `examples/` directory for complete working examples:

- `test_identity.py` - Agent registration
- `test_reputation.py` - Reputation and feedback flow
- `test_validation.py` - Validation requests and responses
- `test_ipfs.py` - IPFS uploading, pinning, and fetching

Run examples:

```bash
# Make sure you have a local Hardhat node running with deployed contracts
python examples/test_identity.py
python examples/test_reputation.py
python examples/test_validation.py
python examples/test_ipfs.py
```

## Architecture

The SDK uses an adapter pattern to support multiple blockchain libraries:

- **Web3Adapter** - For Web3.py v6+

Additional adapters can be implemented by extending the `BlockchainAdapter` interface.

## Development

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Format code
black src/ examples/ tests/

# Type checking
mypy src/
```

## License

MIT

## Specification

For the complete ERC-8004 specification, see [SPEC.md](./SPEC.md).

## Links

- [ERC-8004 Specification](./SPEC.md)
- [ChaosChainsAI](https://chaoschain.ai)
- [GitHub Repository](https://github.com/tetratorus/sdk)

## API Reference

### ERC8004Client

Main client for interacting with ERC-8004 protocol.

```python
client = ERC8004Client(adapter, addresses)
```

**Sub-clients:**
- `client.identity` - IdentityClient
- `client.reputation` - ReputationClient
- `client.validation` - ValidationClient

**Methods:**
- `get_address()` - Get signer address
- `get_chain_id()` - Get chain ID
- `get_addresses()` - Get contract addresses

### IdentityClient

Handles agent registration and identity management.

**Methods:**
- `register()` - Register agent without URI
- `register_with_uri(uri)` - Register with token URI
- `register_with_metadata(uri, metadata)` - Register with URI and metadata
- `get_token_uri(agent_id)` - Get token URI
- `set_token_uri(agent_id, uri)` - Set token URI
- `get_owner(agent_id)` - Get agent owner
- `get_metadata(agent_id, key)` - Get on-chain metadata
- `set_metadata(agent_id, key, value)` - Set on-chain metadata
- `get_registration_file(agent_id)` - Fetch and parse registration file

### ReputationClient

Handles feedback submission and reputation queries.

**Methods:**
- `create_feedback_auth(...)` - Create feedback authorization
- `sign_feedback_auth(auth)` - Sign feedback authorization
- `give_feedback(...)` - Submit feedback
- `revoke_feedback(agent_id, index)` - Revoke feedback
- `append_response(...)` - Append response to feedback
- `get_summary(agent_id, ...)` - Get reputation summary
- `read_feedback(agent_id, client, index)` - Read specific feedback
- `read_all_feedback(agent_id, ...)` - Read all feedback
- `get_clients(agent_id)` - Get all clients who gave feedback
- `get_last_index(agent_id, client)` - Get last feedback index

### ValidationClient

Handles validation requests and responses.

**Methods:**
- `validation_request(...)` - Request validation
- `validation_response(...)` - Provide validation response
- `get_validation_status(request_hash)` - Get validation status
- `get_summary(agent_id, ...)` - Get validation summary
- `get_agent_validations(agent_id)` - Get all validations for agent
- `get_validator_requests(validator)` - Get all requests for validator

### IPFSClient

Client for IPFS operations.

**Methods:**
- `upload(content, name, metadata)` - Upload content
- `upload_json(data, name, metadata)` - Upload JSON
- `pin(cid, name)` - Pin existing CID
- `fetch(cid_or_uri)` - Fetch content
- `fetch_json(cid_or_uri)` - Fetch and parse JSON
- `get_gateway_url(cid)` - Get gateway URL

# ERC-8004 SDK (Python)

Python SDK for interacting with ERC-8004 Trustless Agents protocol.

## Installation

```bash
pip install erc-8004-py
```

## Quick Start

```python
from erc8004 import ERC8004Client, Web3Adapter
from web3 import Web3

# Connect to Ethereum node
w3 = Web3(Web3.HTTPProvider('YOUR_RPC_URL'))
adapter = Web3Adapter(w3, private_key='0x...')

# Initialize client
client = ERC8004Client(
    adapter=adapter,
    addresses={
        'identityRegistry': '0x...',
        'reputationRegistry': '0x...',
        'validationRegistry': '0x...',
        'chainId': 11155111,
    }
)

# Register an agent
result = client.identity.register_with_uri('ipfs://QmYourAgentData')
print(f"Agent ID: {result['agentId']}")
```

## Contract Addresses

### Sepolia Testnet

```python
addresses = {
    'identityRegistry': '0x8004a6090Cd10A7288092483047B097295Fb8847',
    'reputationRegistry': '0x8004B8FD1A363aa02fDC07635C0c5F94f6Af5B7E',
    'validationRegistry': '0x8004CB39f29c09145F24Ad9dDe2A108C1A2cdfC5',
    'chainId': 11155111,
}
```

## Core Features

### Identity Management

```python
# Register an agent
result = client.identity.register_with_uri('ipfs://QmYourAgentData')
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
    int(time.time()) + 3600,
    chain_id,
    signer_address
)

signed_auth = client.reputation.sign_feedback_auth(feedback_auth)

# Submit feedback
client.reputation.give_feedback(
    agent_id=agent_id,
    score=95,
    tag1='excellent-service',
    tag2='fast-response',
    feedback_auth=signed_auth,
)

# Get reputation summary
summary = client.reputation.get_summary(agent_id)
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
    response=100,
    response_uri='ipfs://QmValidationResponse',
    tag='zkML-proof',
)
```

## IPFS Integration

```python
from erc8004 import IPFSClientConfig, create_ipfs_client, cid_to_bytes32

# Create IPFS client
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
    'endpoints': [],
}

result = ipfs.upload_json(agent_data)
client.identity.register_with_uri(result.uri)

# Convert CID to bytes32
hash_bytes = cid_to_bytes32(result.cid)
```

## API Reference

### ERC8004Client

Main client with three sub-clients:
- `client.identity` - Agent registration and identity
- `client.reputation` - Feedback and reputation
- `client.validation` - Validation requests and responses

### IdentityClient

- `register()` - Register agent without URI
- `register_with_uri(uri)` - Register with token URI
- `register_with_metadata(uri, metadata)` - Register with URI and metadata
- `get_token_uri(agent_id)` - Get token URI
- `get_owner(agent_id)` - Get agent owner
- `get_metadata(agent_id, key)` - Get on-chain metadata
- `set_metadata(agent_id, key, value)` - Set on-chain metadata

### ReputationClient

- `create_feedback_auth(...)` - Create feedback authorization
- `sign_feedback_auth(auth)` - Sign feedback authorization
- `give_feedback(...)` - Submit feedback
- `revoke_feedback(agent_id, index)` - Revoke feedback
- `get_summary(agent_id, ...)` - Get reputation summary
- `read_feedback(agent_id, client, index)` - Read specific feedback
- `get_clients(agent_id)` - Get all clients who gave feedback
- `get_last_index(agent_id, client)` - Get last feedback index

### ValidationClient

- `validation_request(...)` - Request validation
- `validation_response(...)` - Provide validation response
- `get_validation_status(request_hash)` - Get validation status
- `get_summary(agent_id, ...)` - Get validation summary
- `get_agent_validations(agent_id)` - Get all validations for agent

### IPFSClient

- `upload(content, name, metadata)` - Upload content
- `upload_json(data, name, metadata)` - Upload JSON
- `pin(cid, name)` - Pin existing CID
- `fetch(cid_or_uri)` - Fetch content
- `fetch_json(cid_or_uri)` - Fetch and parse JSON

## Links

- [ERC-8004 Specification](https://eips.ethereum.org/EIPS/eip-8004)
- [GitHub Repository](https://github.com/tetratorus/sdk)

## License

MIT

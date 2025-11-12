# IPFS Guide for ERC-8004 SDK

Complete guide to using IPFS with the ERC-8004 Python SDK.

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Providers](#providers)
  - [Pinata](#pinata)
  - [NFT.Storage](#nftstorage)
  - [Web3.Storage](#web3storage)
  - [Local IPFS Node](#local-ipfs-node)
- [Uploading Content](#uploading-content)
- [Pinning Content](#pinning-content)
- [Fetching Content](#fetching-content)
- [CID Conversion](#cid-conversion)
- [Best Practices](#best-practices)

## Overview

IPFS (InterPlanetary File System) is a distributed file system that enables content-addressed storage. The ERC-8004 SDK provides comprehensive IPFS support for:

- Uploading agent registration files
- Storing feedback data
- Sharing validation requests and responses
- Converting IPFS CIDs to bytes32 for on-chain use

## Quick Start

```python
from erc8004 import IPFSClientConfig, create_ipfs_client

# Create IPFS client
config = IPFSClientConfig(
    provider='pinata',
    api_key='YOUR_API_KEY',
    api_secret='YOUR_API_SECRET',
)
ipfs = create_ipfs_client(config)

# Upload JSON
data = {'name': 'My Agent', 'description': 'Test agent'}
result = ipfs.upload_json(data)
print(f"Uploaded to: {result.uri}")
```

## Providers

### Pinata

[Pinata](https://pinata.cloud/) is a popular IPFS pinning service with generous free tier.

**Setup:**

1. Sign up at https://pinata.cloud/
2. Generate API keys from your account dashboard
3. Configure the client:

```python
from erc8004 import IPFSClientConfig, create_ipfs_client

config = IPFSClientConfig(
    provider='pinata',
    api_key='YOUR_PINATA_API_KEY',
    api_secret='YOUR_PINATA_API_SECRET',
    gateway_url='https://gateway.pinata.cloud/ipfs/',  # Optional custom gateway
)
ipfs = create_ipfs_client(config)
```

**Features:**
- ✅ Upload files
- ✅ Upload JSON
- ✅ Pin existing CIDs
- ✅ Custom metadata
- ✅ Free tier: 1 GB storage

**Example:**

```python
# Upload with metadata
result = ipfs.upload_json(
    data={'type': 'agent-registration'},
    name='my-agent.json',
    metadata={'environment': 'production', 'version': '1.0'}
)

# Pin existing CID
ipfs.pin('QmExistingCID', name='important-file')
```

### NFT.Storage

[NFT.Storage](https://nft.storage/) provides free IPFS storage backed by Filecoin.

**Setup:**

1. Sign up at https://nft.storage/
2. Generate an API token
3. Configure the client:

```python
config = IPFSClientConfig(
    provider='nftstorage',
    api_key='YOUR_NFT_STORAGE_API_KEY',
)
ipfs = create_ipfs_client(config)
```

**Features:**
- ✅ Upload files
- ✅ Upload JSON
- ❌ Pin existing CIDs (not supported)
- ✅ Free tier: Unlimited storage

**Example:**

```python
# Upload agent registration
agent_data = {
    'type': 'https://eips.ethereum.org/EIPS/eip-8004#registration-v1',
    'name': 'My Agent',
    'description': 'Agent description',
}

result = ipfs.upload_json(agent_data)
print(f"CID: {result.cid}")
```

### Web3.Storage

[Web3.Storage](https://web3.storage/) is another Filecoin-backed IPFS service.

**Setup:**

1. Sign up at https://web3.storage/
2. Generate an API token
3. Configure the client:

```python
config = IPFSClientConfig(
    provider='web3storage',
    api_key='YOUR_WEB3_STORAGE_API_KEY',
)
ipfs = create_ipfs_client(config)
```

**Features:**
- ✅ Upload files
- ✅ Upload JSON
- ❌ Pin existing CIDs (not supported)
- ✅ Free tier: Unlimited storage

### Local IPFS Node

Run your own IPFS node for complete control.

**Setup:**

1. Install IPFS: https://docs.ipfs.tech/install/
2. Start the daemon: `ipfs daemon`
3. Configure the client:

```python
config = IPFSClientConfig(
    provider='ipfs',
    node_url='http://127.0.0.1:5001',  # Default
    gateway_url='http://127.0.0.1:8080/ipfs/',  # Default
)
ipfs = create_ipfs_client(config)
```

**Features:**
- ✅ Upload files
- ✅ Upload JSON
- ✅ Pin existing CIDs
- ✅ Complete control
- ✅ No external dependencies

**Example:**

```python
# Upload to local node
result = ipfs.upload_json({'data': 'my data'})

# Pin existing CID from the network
ipfs.pin('QmExistingCID')
```

## Uploading Content

### Upload String or Bytes

```python
# Upload string
result = ipfs.upload("Hello, IPFS!", name="greeting.txt")

# Upload bytes
data = b"Binary data here"
result = ipfs.upload(data, name="data.bin")

print(f"CID: {result.cid}")
print(f"URI: {result.uri}")
print(f"URL: {result.url}")
```

### Upload JSON

```python
# Agent registration file
agent_data = {
    'type': 'https://eips.ethereum.org/EIPS/eip-8004#registration-v1',
    'name': 'MyAgent',
    'description': 'Description of my agent',
    'image': 'https://example.com/agent.png',
    'endpoints': [
        {
            'name': 'A2A',
            'endpoint': 'https://agent.example/.well-known/agent-card.json',
            'version': '0.3.0'
        }
    ],
    'supportedTrust': ['reputation', 'validation']
}

result = ipfs.upload_json(agent_data, name='agent-registration.json')

# Use in contract
client.identity.register_with_uri(result.uri)
```

### Upload Feedback Data

```python
# Feedback file
feedback_data = {
    'agentRegistry': 'eip155:1:0x...',
    'agentId': 22,
    'clientAddress': 'eip155:1:0x...',
    'createdAt': '2025-09-23T12:00:00Z',
    'feedbackAuth': '0x...',
    'score': 95,
    'tag1': 'excellent',
    'tag2': 'fast',
    'skill': 'code-generation',
    'proof_of_payment': {
        'fromAddress': '0x...',
        'toAddress': '0x...',
        'chainId': '1',
        'txHash': '0x...'
    }
}

result = ipfs.upload_json(feedback_data)
print(f"Feedback URI: {result.uri}")
```

## Pinning Content

Pinning ensures content remains available on the IPFS network.

```python
# Pin existing CID
ipfs.pin('QmExistingCID', name='important-agent-data')

# Note: Only Pinata and local IPFS support pinning
# NFT.Storage and Web3.Storage automatically persist uploaded content
```

## Fetching Content

### Fetch Text Content

```python
# Fetch by CID
content = ipfs.fetch('QmYourCID')
print(content)

# Fetch by URI
content = ipfs.fetch('ipfs://QmYourCID')
print(content)
```

### Fetch JSON

```python
# Fetch and parse JSON
data = ipfs.fetch_json('QmYourCID')
print(data['name'])

# Fetch agent registration file
agent_id = 1
uri = client.identity.get_token_uri(agent_id)
registration = ipfs.fetch_json(uri)
print(f"Agent: {registration['name']}")
```

### Custom Gateway

```python
# Use a specific gateway
config = IPFSClientConfig(
    provider='ipfs',
    gateway_url='https://cloudflare-ipfs.com/ipfs/'
)
ipfs = create_ipfs_client(config)

content = ipfs.fetch('QmYourCID')
```

## CID Conversion

Convert IPFS CIDs to bytes32 for on-chain storage (e.g., validation request hashes).

### Basic Conversion

```python
from erc8004 import cid_to_bytes32, ipfs_uri_to_bytes32

# From CID
cid = 'QmR7GSQM93Cx5eAg6a6yRzNde1FQv7uL6X1o4k7zrJa3LX'
bytes32 = cid_to_bytes32(cid)
print(f"Bytes32: {bytes32}")

# From URI
uri = 'ipfs://QmR7GSQM93Cx5eAg6a6yRzNde1FQv7uL6X1o4k7zrJa3LX'
bytes32 = ipfs_uri_to_bytes32(uri)
print(f"Bytes32: {bytes32}")
```

### Use in Validation

```python
# Upload validation request
request_data = {
    'agentId': 1,
    'input': 'test input',
    'output': 'test output',
    'timestamp': '2025-01-15T12:00:00Z'
}

result = ipfs.upload_json(request_data)

# Convert CID to bytes32 for on-chain use
request_hash = cid_to_bytes32(result.cid)

# Submit validation request
client.validation.validation_request(
    validator_address='0x...',
    agent_id=1,
    request_uri=result.uri,
    request_hash=request_hash
)
```

### Technical Details

The conversion works as follows:

1. CIDv0 format: `Qm...` (base58 encoded)
2. Decoded structure: `[0x12, 0x20, ...32 bytes...]`
   - `0x12` = SHA-256 hash function
   - `0x20` = 32 bytes length
   - Following 32 bytes = actual hash
3. Extract the 32-byte hash for on-chain use

**Note:** Currently only CIDv0 (starting with "Qm") is supported.

## Best Practices

### 1. Choose the Right Provider

- **Pinata**: Best for production with custom metadata needs
- **NFT.Storage**: Best for free unlimited storage
- **Web3.Storage**: Alternative to NFT.Storage
- **Local Node**: Best for development and testing

### 2. Handle Errors Gracefully

```python
try:
    result = ipfs.upload_json(data)
    print(f"Success: {result.uri}")
except Exception as error:
    print(f"Upload failed: {error}")
    # Fallback to alternative provider or retry
```

### 3. Use Appropriate Gateways

```python
# For production, use reliable gateways
gateways = [
    'https://gateway.pinata.cloud/ipfs/',
    'https://cloudflare-ipfs.com/ipfs/',
    'https://ipfs.io/ipfs/',
]

# Try multiple gateways if one fails
for gateway in gateways:
    try:
        config = IPFSClientConfig(provider='ipfs', gateway_url=gateway)
        ipfs = create_ipfs_client(config)
        content = ipfs.fetch(cid)
        break
    except Exception:
        continue
```

### 4. Validate Content

```python
# Always validate fetched JSON structure
registration = ipfs.fetch_json(uri)

required_fields = ['type', 'name', 'description']
for field in required_fields:
    if field not in registration:
        raise ValueError(f"Missing required field: {field}")

# Verify type field
expected_type = 'https://eips.ethereum.org/EIPS/eip-8004#registration-v1'
if registration['type'] != expected_type:
    raise ValueError(f"Invalid type: {registration['type']}")
```

### 5. Cache Frequently Accessed Content

```python
import json
from pathlib import Path

cache_dir = Path('.ipfs_cache')
cache_dir.mkdir(exist_ok=True)

def fetch_with_cache(ipfs, cid):
    cache_file = cache_dir / f"{cid}.json"

    # Check cache first
    if cache_file.exists():
        with open(cache_file, 'r') as f:
            return json.load(f)

    # Fetch from IPFS
    data = ipfs.fetch_json(cid)

    # Cache for next time
    with open(cache_file, 'w') as f:
        json.dump(data, f)

    return data
```

### 6. Monitor Costs

- Pinata: Check usage against plan limits
- NFT.Storage / Web3.Storage: Free but monitor rate limits
- Local node: Monitor disk space

### 7. Security Considerations

- Never upload sensitive data without encryption
- Validate all fetched content before use
- Use HTTPS gateways to prevent MITM attacks
- Consider using signed/encrypted content for sensitive operations

## Environment Variables

Use environment variables for API keys:

```python
import os
from dotenv import load_dotenv

load_dotenv()

config = IPFSClientConfig(
    provider='pinata',
    api_key=os.getenv('PINATA_API_KEY'),
    api_secret=os.getenv('PINATA_API_SECRET'),
)
```

`.env` file:
```
PINATA_API_KEY=your_key_here
PINATA_API_SECRET=your_secret_here
```

## Troubleshooting

### Upload Fails

1. Check API credentials
2. Verify network connectivity
3. Check rate limits
4. Try a different provider

### Fetch Fails

1. Try different gateway
2. Verify CID is valid
3. Check if content is pinned
4. Wait and retry (content may be propagating)

### Slow Fetches

1. Use faster gateway (Cloudflare, Pinata)
2. Pin frequently accessed content
3. Implement local caching
4. Consider CDN for hot content

## Examples

See `examples/test_ipfs.py` for complete working examples.

## Resources

- [IPFS Documentation](https://docs.ipfs.tech/)
- [Pinata Documentation](https://docs.pinata.cloud/)
- [NFT.Storage Documentation](https://nft.storage/docs/)
- [Web3.Storage Documentation](https://web3.storage/docs/)
- [ERC-8004 Specification](https://eips.ethereum.org/EIPS/eip-8004)

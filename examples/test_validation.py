"""
Example script to test ERC-8004 Validation functionality

Prerequisites:
1. Run hardhat node: npx hardhat node
2. Deploy contracts with the ignition script

This example demonstrates:
- Requesting validation from a validator
- Providing validation responses
- Reading validation status
"""

import secrets
from erc8004 import ERC8004Client, Web3Adapter, ipfs_uri_to_bytes32
from web3 import Web3

# Contract addresses - CREATE2 vanity addresses (same on all networks)
IDENTITY_REGISTRY = "0x8004AbdDA9b877187bF865eD1d8B5A41Da3c4997"
REPUTATION_REGISTRY = "0x8004B312333aCb5764597c2BeEe256596B5C6876"
VALIDATION_REGISTRY = "0x8004C8AEF64521bC97AB50799d394CDb785885E3"

# Base58 alphabet for CIDv0 encoding
BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def generate_random_cidv0() -> str:
    """
    Generate a random CIDv0 (Qm...) for testing purposes
    CIDv0 format: base58(0x12 + 0x20 + 32 random bytes)
    """
    # Create random 32 bytes
    random_bytes = secrets.token_bytes(32)

    # Build CIDv0 structure: [0x12 (sha256), 0x20 (32 bytes), ...random bytes...]
    cid_bytes = bytearray([0x12, 0x20])
    cid_bytes.extend(random_bytes)

    # Encode to base58
    num = int.from_bytes(cid_bytes, 'big')

    encoded = ''
    while num > 0:
        remainder = num % 58
        encoded = BASE58_ALPHABET[remainder] + encoded
        num = num // 58

    # Handle leading zeros
    for byte in cid_bytes:
        if byte == 0:
            encoded = '1' + encoded
        else:
            break

    return encoded


def main():
    print("🚀 ERC-8004 Validation Test\n")

    # Connect to local Hardhat
    print("Connecting to local Hardhat...")
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

    # Use first account as agent owner (hardhat account 0)
    agent_owner_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    # Use second account as validator (hardhat account 1)
    validator_key = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"

    agent_adapter = Web3Adapter(w3, private_key=agent_owner_key)
    validator_adapter = Web3Adapter(w3, private_key=validator_key)

    agent_owner_address = agent_adapter.get_address()
    validator_address = validator_adapter.get_address()

    print(f"Agent Owner: {agent_owner_address}")
    print(f"Validator: {validator_address}\n")

    # Create SDK instances
    agent_sdk = ERC8004Client(
        adapter=agent_adapter,
        addresses={
            "identityRegistry": IDENTITY_REGISTRY,
            "reputationRegistry": REPUTATION_REGISTRY,
            "validationRegistry": VALIDATION_REGISTRY,
            "chainId": 31337,
        },
    )

    validator_sdk = ERC8004Client(
        adapter=validator_adapter,
        addresses={
            "identityRegistry": IDENTITY_REGISTRY,
            "reputationRegistry": REPUTATION_REGISTRY,
            "validationRegistry": VALIDATION_REGISTRY,
            "chainId": 31337,
        },
    )

    # Step 1: Register an agent
    print("📋 Step 1: Registering an agent...")
    register_result = agent_sdk.identity.register_with_uri("https://example.com/agent.json")
    agent_id = register_result["agentId"]
    print(f"✅ Agent registered with ID: {agent_id}")
    print(f"   TX Hash: {register_result['txHash']}\n")

    # Step 2: Request validation
    print("📋 Step 2: Agent requesting validation...")
    # Generate a random IPFS CID for this validation request
    cid1 = generate_random_cidv0()
    request_uri = f"ipfs://{cid1}"
    # Convert IPFS CID to bytes32 for use as requestHash
    request_hash = ipfs_uri_to_bytes32(request_uri)

    validation_request_result = agent_sdk.validation.validation_request(
        validator_address, agent_id, request_uri, request_hash
    )
    print("✅ Validation requested")
    print(f"   Validator: {validator_address}")
    print(f"   Request URI: {request_uri}")
    print(f"   Request Hash: {validation_request_result['requestHash']}")
    print(f"   TX Hash: {validation_request_result['txHash']}\n")

    # Step 3: Validator provides response (passed)
    print("📋 Step 3: Validator providing response (passed)...")
    response_uri1 = f"ipfs://{generate_random_cidv0()}"
    response_result = validator_sdk.validation.validation_response(
        request_hash=request_hash,
        response=100,  # 100 = passed, 0 = failed
        response_uri=response_uri1,
        tag="zkML-proof",
    )
    print("✅ Validation response provided")
    print(f"   Response: 100 (passed)")
    print(f"   Tag: zkML-proof")
    print(f"   TX Hash: {response_result['txHash']}\n")

    # Step 4: Read validation status
    print("📋 Step 4: Reading validation status...")
    status = agent_sdk.validation.get_validation_status(request_hash)
    print("✅ Validation status retrieved:")
    print(f"   Validator: {status['validatorAddress']}")
    print(f"   Agent ID: {status['agentId']}")
    print(f"   Response: {status['response']} / 100")
    print(f"   Tag: {status['tag']}")
    print(f"   Last Update: {status['lastUpdate']}\n")

    # Step 5: Get validation summary for agent
    print("📋 Step 5: Getting validation summary for agent...")
    summary = agent_sdk.validation.get_summary(agent_id, [validator_address])
    print("✅ Validation summary:")
    print(f"   Validation Count: {summary['count']}")
    print(f"   Average Response: {summary['avgResponse']} / 100\n")

    # Step 6: Get all validation requests for agent
    print("📋 Step 6: Getting all validations for agent...")
    agent_validations = agent_sdk.validation.get_agent_validations(agent_id)
    print("✅ Agent validations retrieved:")
    print(f"   Total validations: {len(agent_validations)}")
    for i, req_hash in enumerate(agent_validations):
        print(f"   [{i}] Request Hash: {req_hash}")
    print()

    # Step 7: Get all requests handled by validator
    print("📋 Step 7: Getting all requests for validator...")
    validator_requests = validator_sdk.validation.get_validator_requests(validator_address)
    print("✅ Validator requests retrieved:")
    print(f"   Total requests: {len(validator_requests)}")
    for i, req_hash in enumerate(validator_requests):
        print(f"   [{i}] Request Hash: {req_hash}")
    print()

    # Step 8: Submit second validation request and provide different response
    print("📋 Step 8: Submitting second validation request...")
    # Generate another random IPFS CID
    cid2 = generate_random_cidv0()
    request_uri2 = f"ipfs://{cid2}"
    request_hash2 = ipfs_uri_to_bytes32(request_uri2)
    request2 = agent_sdk.validation.validation_request(
        validator_address, agent_id, request_uri2, request_hash2
    )
    print("✅ Second validation requested")
    print(f"   Request Hash: {request2['requestHash']}\n")

    # Validator provides partial success response
    print("📋 Step 9: Validator providing partial response...")
    validator_sdk.validation.validation_response(
        request_hash=request2["requestHash"],
        response=75,  # Partial success
        tag="tee-attestation",
    )
    print("✅ Response provided (75 - partial success)\n")

    # Step 10: Get updated summary
    print("📋 Step 10: Getting updated validation summary...")
    updated_summary = agent_sdk.validation.get_summary(agent_id)
    print("✅ Updated validation summary:")
    print(f"   Validation Count: {updated_summary['count']}")
    print(f"   Average Response: {updated_summary['avgResponse']} / 100\n")

    # Step 11: Validator updates first validation (progressive validation)
    print("📋 Step 11: Validator updating first validation (hard finality)...")
    response_uri2 = f"ipfs://{generate_random_cidv0()}"
    validator_sdk.validation.validation_response(
        request_hash=request_hash,
        response=100,
        tag="hard-finality",
        response_uri=response_uri2,
    )
    print("✅ Validation updated with hard finality tag\n")

    updated_status = agent_sdk.validation.get_validation_status(request_hash)
    print(f"   Updated tag: {updated_status['tag']}")

    print("\n🎉 All tests completed successfully!")


if __name__ == "__main__":
    main()

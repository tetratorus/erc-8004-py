"""
Example script to test ERC-8004 SDK with ChaosChain Sepolia testnet

Prerequisites:
1. Set up environment variables in .env file:
   - SEPOLIA_RPC_URL: Your Sepolia RPC endpoint
   - SEPOLIA_TESTNET_PRIVATE_KEY_1: Agent owner private key
   - SEPOLIA_TESTNET_PRIVATE_KEY_2: Feedback giver private key

This example demonstrates:
- Initializing the SDK with adapter pattern
- Registering agents
- Reading agent information
- Updating tokenURI
- Creating and signing feedbackAuth
- Submitting feedback
- Validation workflow
"""

import os
import secrets
import time
from erc8004 import ERC8004Client, Web3Adapter, ipfs_uri_to_bytes32
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Contract addresses from ChaosChain deployment
IDENTITY_REGISTRY = "0x7177a6867296406881E20d6647232314736Dd09A"
REPUTATION_REGISTRY = "0xB5048e3ef1DA4E04deB6f7d0423D06F63869e322"
VALIDATION_REGISTRY = "0x662b40A526cb4017d947e71eAF6753BF3eeE66d8"

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
    print("🚀 ERC-8004 SDK Test with ChaosChain Sepolia\n")

    # Connect to Sepolia
    print("Connecting to Sepolia...")
    sepolia_rpc = os.getenv("SEPOLIA_RPC_URL", "")
    if not sepolia_rpc:
        print("❌ Error: SEPOLIA_RPC_URL not set in .env file")
        return

    w3 = Web3(Web3.HTTPProvider(sepolia_rpc))

    if not w3.is_connected():
        print("❌ Error: Failed to connect to Sepolia")
        return

    # Get private keys from environment
    agent_owner_key = os.getenv("SEPOLIA_TESTNET_PRIVATE_KEY_1", "")
    feedback_giver_key = os.getenv("SEPOLIA_TESTNET_PRIVATE_KEY_2", "")

    if not agent_owner_key or not feedback_giver_key:
        print("❌ Error: Private keys not set in .env file")
        print("   Required: SEPOLIA_TESTNET_PRIVATE_KEY_1 and SEPOLIA_TESTNET_PRIVATE_KEY_2")
        return

    # Create adapters
    agent_adapter = Web3Adapter(w3, private_key=agent_owner_key)
    feedback_adapter = Web3Adapter(w3, private_key=feedback_giver_key)

    agent_owner_address = agent_adapter.get_address()
    feedback_giver_address = feedback_adapter.get_address()

    print(f"Agent Owner: {agent_owner_address}")
    print(f"Feedback Giver: {feedback_giver_address}\n")

    # Create SDK instances
    client = ERC8004Client(
        adapter=agent_adapter,
        addresses={
            "identityRegistry": IDENTITY_REGISTRY,
            "reputationRegistry": REPUTATION_REGISTRY,
            "validationRegistry": VALIDATION_REGISTRY,
            "chainId": 11155111,  # Sepolia chain ID
        },
    )

    feedback_client = ERC8004Client(
        adapter=feedback_adapter,
        addresses={
            "identityRegistry": IDENTITY_REGISTRY,
            "reputationRegistry": REPUTATION_REGISTRY,
            "validationRegistry": VALIDATION_REGISTRY,
            "chainId": 11155111,
        },
    )

    # Test 1: Register agent with URI and metadata
    print("Test 1: Register agent with URI and on-chain metadata")
    try:
        registration_uri = f"ipfs://{generate_random_cidv0()}"
        metadata = [
            {"key": "agentName", "value": "TestAgent"},
            {"key": "agentWallet", "value": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb7"}
        ]

        result1 = client.identity.register_with_metadata(registration_uri, metadata)
        print(f"✅ Registered agent ID: {result1['agentId']}")
        print(f"   TX Hash: {result1['txHash']}")
        print(f"   🔍 View on Etherscan: https://sepolia.etherscan.io/tx/{result1['txHash']}")
        print(f"   Owner: {client.identity.get_owner(result1['agentId'])}")
        print(f"   URI: {client.identity.get_token_uri(result1['agentId'])}")

        # Read back metadata
        agent_name = client.identity.get_metadata(result1["agentId"], "agentName")
        agent_wallet = client.identity.get_metadata(result1["agentId"], "agentWallet")
        print(f"   Metadata - agentName: {agent_name}")
        print(f"   Metadata - agentWallet: {agent_wallet}\n")
    except Exception as error:
        print(f"❌ Error: {error}\n")

    # Test 2: Set metadata after registration
    print("Test 2: Set metadata after registration")
    try:
        result2 = client.identity.register()
        print(f"✅ Registered agent ID: {result2['agentId']}")
        print(f"   TX Hash: {result2['txHash']}")
        print(f"   🔍 View on Etherscan: https://sepolia.etherscan.io/tx/{result2['txHash']}")

        set_metadata_result = client.identity.set_metadata(result2["agentId"], "status", "active")
        status = client.identity.get_metadata(result2["agentId"], "status")
        print(f"   Set metadata - status: {status}")
        print(f"   TX Hash: {set_metadata_result['txHash']}")
        print(f"   🔍 View on Etherscan: https://sepolia.etherscan.io/tx/{set_metadata_result['txHash']}\n")
    except Exception as error:
        print(f"❌ Error: {error}\n")

    # Test 3: Create feedbackAuth and submit feedback
    print("Test 3: Create feedbackAuth and submit feedback")
    try:
        result3 = client.identity.register()
        agent_id = result3["agentId"]
        print(f"✅ Registered agent ID: {agent_id}")
        print(f"   TX Hash: {result3['txHash']}")
        print(f"   🔍 View on Etherscan: https://sepolia.etherscan.io/tx/{result3['txHash']}")

        # Get chain ID
        chain_id = client.get_chain_id()

        # Get the last feedback index for the feedback giver
        last_index = client.reputation.get_last_index(agent_id, feedback_giver_address)
        print(f"   Last feedback index: {last_index}")

        # Create feedbackAuth (agent owner authorizes feedback giver)
        feedback_auth = client.reputation.create_feedback_auth(
            agent_id,
            feedback_giver_address,
            last_index + 1,  # Allow next feedback
            int(time.time()) + 3600,  # Valid for 1 hour
            chain_id,
            agent_owner_address
        )
        print(f"✅ FeedbackAuth created (indexLimit: {feedback_auth['indexLimit']})")

        # Agent owner signs the feedbackAuth
        signed_auth = client.reputation.sign_feedback_auth(feedback_auth)
        print(f"✅ FeedbackAuth signed: {signed_auth[:20]}...")

        # Feedback giver submits feedback
        feedback_result = feedback_client.reputation.give_feedback(
            agent_id=agent_id,
            score=95,
            tag1="excellent",
            tag2="reliable",
            feedback_auth=signed_auth,
        )
        print(f"✅ Feedback submitted!")
        print(f"   Score: 95 / 100")
        print(f"   Tags: excellent, reliable")
        print(f"   TX Hash: {feedback_result['txHash']}")
        print(f"   🔍 View on Etherscan: https://sepolia.etherscan.io/tx/{feedback_result['txHash']}")

        # Read the feedback back
        feedback = feedback_client.reputation.read_feedback(
            agent_id,
            feedback_giver_address,
            last_index + 1  # Use the new index after submission
        )
        print(f"✅ Feedback retrieved:")
        print(f"   Score: {feedback['score']} / 100")
        print(f"   Tag1: {feedback['tag1']}")
        print(f"   Tag2: {feedback['tag2']}")

        # Get reputation summary
        summary = client.reputation.get_summary(agent_id)
        print(f"✅ Reputation summary:")
        print(f"   Feedback Count: {summary['count']}")
        print(f"   Average Score: {summary['averageScore']} / 100\n")
    except Exception as error:
        print(f"❌ Error: {error}\n")

    # Test 4: Validation workflow
    print("Test 4: Validation workflow")
    try:
        # Register a new agent for validation testing
        result4 = client.identity.register()
        validation_agent_id = result4["agentId"]
        print(f"✅ Registered agent ID for validation: {validation_agent_id}")
        print(f"   TX Hash: {result4['txHash']}")
        print(f"   🔍 View on Etherscan: https://sepolia.etherscan.io/tx/{result4['txHash']}")

        # Generate a random IPFS CID for the validation request
        validation_cid = generate_random_cidv0()
        request_uri = f"ipfs://{validation_cid}"
        request_hash = ipfs_uri_to_bytes32(request_uri)

        # Request validation from feedback giver (acting as validator)
        request_result = client.validation.validation_request(
            feedback_giver_address,
            validation_agent_id,
            request_uri,
            request_hash,
        )
        print(f"✅ Validation requested")
        print(f"   Validator: {feedback_giver_address}")
        print(f"   Request URI: {request_uri}")
        print(f"   Request Hash: {request_result['requestHash']}")
        print(f"   TX Hash: {request_result['txHash']}")
        print(f"   🔍 View on Etherscan: https://sepolia.etherscan.io/tx/{request_result['txHash']}")

        # Validator (feedback giver) provides response
        response_uri = f"ipfs://{generate_random_cidv0()}"
        response_result = feedback_client.validation.validation_response(
            request_hash=request_hash,
            response=100,  # 100 = passed
            response_uri=response_uri,
            tag="zkML-proof",
        )
        print(f"✅ Validation response provided")
        print(f"   Response: 100 (passed)")
        print(f"   Tag: zkML-proof")
        print(f"   Response URI: {response_uri}")
        print(f"   TX Hash: {response_result['txHash']}")
        print(f"   🔍 View on Etherscan: https://sepolia.etherscan.io/tx/{response_result['txHash']}")

        # Read validation status
        status = client.validation.get_validation_status(request_hash)
        print(f"✅ Validation status retrieved:")
        print(f"   Validator: {status['validatorAddress']}")
        print(f"   Agent ID: {status['agentId']}")
        print(f"   Response: {status['response']} / 100")
        print(f"   Tag: {status['tag']}")
        print(f"   Last Update: {status['lastUpdate']}")

        # Get validation summary for agent
        validation_summary = client.validation.get_summary(validation_agent_id, [feedback_giver_address])
        print(f"✅ Validation summary:")
        print(f"   Validation Count: {validation_summary['count']}")
        print(f"   Average Response: {validation_summary['avgResponse']} / 100")

        # Get all validation requests for agent
        agent_validations = client.validation.get_agent_validations(validation_agent_id)
        print(f"✅ Agent validations retrieved:")
        print(f"   Total validations: {len(agent_validations)}")
        for i, req_hash in enumerate(agent_validations):
            print(f"   [{i}] Request Hash: {req_hash}")

        # Get all requests handled by validator
        validator_requests = feedback_client.validation.get_validator_requests(feedback_giver_address)
        print(f"✅ Validator requests retrieved:")
        print(f"   Total requests: {len(validator_requests)}")
        for i, req_hash in enumerate(validator_requests):
            print(f"   [{i}] Request Hash: {req_hash}")
        print()
    except Exception as error:
        print(f"❌ Error: {error}\n")

    print("✨ All tests completed!")


if __name__ == "__main__":
    main()

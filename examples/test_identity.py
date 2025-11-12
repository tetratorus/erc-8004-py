"""
Example script to test ERC-8004 SDK with local Hardhat chain

Prerequisites:
1. Run hardhat node: npx hardhat node
2. Deploy contracts with the ignition script

This example demonstrates:
- Initializing the SDK with adapter pattern
- Registering agents
- Reading agent information
- Updating tokenURI
"""

from erc8004 import ERC8004Client, Web3Adapter
from web3 import Web3

# Contract addresses - CREATE2 vanity addresses (same on all networks)
IDENTITY_REGISTRY = "0x8004AbdDA9b877187bF865eD1d8B5A41Da3c4997"
REPUTATION_REGISTRY = "0x8004B312333aCb5764597c2BeEe256596B5C6876"
VALIDATION_REGISTRY = "0x8004C8AEF64521bC97AB50799d394CDb785885E3"


def main():
    print("🚀 ERC-8004 SDK Test\n")

    # Connect to local Hardhat
    print("Connecting to local Hardhat...")
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

    # Use first hardhat account (hardhat default private key)
    private_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

    # Create adapter
    adapter = Web3Adapter(w3, private_key=private_key)

    # Initialize SDK with adapter
    client = ERC8004Client(
        adapter=adapter,
        addresses={
            "identityRegistry": IDENTITY_REGISTRY,
            "reputationRegistry": REPUTATION_REGISTRY,
            "validationRegistry": VALIDATION_REGISTRY,
            "chainId": 31337,  # Hardhat chain ID
        },
    )

    signer_address = client.get_address()
    print(f"Connected with signer: {signer_address}\n")

    # Test 1: Register agent with no URI, then set URI
    print("Test 1: Register agent with no URI, then set URI")
    try:
        result1 = client.identity.register()
        print(f"✅ Registered agent ID: {result1['agentId']}")
        print(f"   TX Hash: {result1['txHash']}")
        print(f"   Owner: {client.identity.get_owner(result1['agentId'])}")

        # Set the tokenURI after registration
        new_uri = "ipfs://QmNewAgent456"
        client.identity.set_agent_uri(result1["agentId"], new_uri)
        print(f"✅ Set tokenURI to: {new_uri}")

        # Verify it was set
        retrieved_uri = client.identity.get_token_uri(result1["agentId"])
        print(f"   Retrieved URI: {retrieved_uri}\n")
    except Exception as error:
        print(f"❌ Error: {error}\n")

    # Test 2: Register agent with URI
    print("Test 2: Register agent with URI")
    try:
        # Example registration file (in production, this would be hosted)
        registration_uri = "https://example.com/agent1.json"
        result2 = client.identity.register_with_uri(registration_uri)
        print(f"✅ Registered agent ID: {result2['agentId']}")
        print(f"   TX Hash: {result2['txHash']}")
        print(f"   Owner: {client.identity.get_owner(result2['agentId'])}")
        print(f"   URI: {client.identity.get_token_uri(result2['agentId'])}\n")
    except Exception as error:
        print(f"❌ Error: {error}\n")

    # Test 3: Register agent with URI and metadata
    print("Test 3: Register agent with URI and on-chain metadata")
    try:
        registration_uri = "ipfs://QmExample123"
        metadata = [
            {"key": "agentName", "value": "TestAgent"},
            {"key": "agentWallet", "value": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb7"},
        ]

        result3 = client.identity.register_with_metadata(registration_uri, metadata)
        print(f"✅ Registered agent ID: {result3['agentId']}")
        print(f"   TX Hash: {result3['txHash']}")
        print(f"   Owner: {client.identity.get_owner(result3['agentId'])}")
        print(f"   URI: {client.identity.get_token_uri(result3['agentId'])}")

        # Read back metadata
        agent_name = client.identity.get_metadata(result3["agentId"], "agentName")
        agent_wallet = client.identity.get_metadata(result3["agentId"], "agentWallet")
        print(f"   Metadata - agentName: {agent_name}")
        print(f"   Metadata - agentWallet: {agent_wallet}\n")
    except Exception as error:
        print(f"❌ Error: {error}\n")

    # Test 4: Set metadata after registration
    print("Test 4: Set metadata after registration")
    try:
        result4 = client.identity.register()
        print(f"✅ Registered agent ID: {result4['agentId']}")

        client.identity.set_metadata(result4["agentId"], "status", "active")
        status = client.identity.get_metadata(result4["agentId"], "status")
        print(f"   Set metadata - status: {status}\n")
    except Exception as error:
        print(f"❌ Error: {error}\n")

    print("✨ All tests completed!")


if __name__ == "__main__":
    main()

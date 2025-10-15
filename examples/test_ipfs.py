"""
Example: IPFS Upload and Pinning

This example demonstrates how to use the IPFS client to:
- Upload files and JSON data to IPFS
- Pin content to keep it available
- Fetch content from IPFS
- Register agents with IPFS-hosted metadata
"""

import os
import json
from erc8004 import (
    IPFSClientConfig,
    cid_to_bytes32,
    create_ipfs_client,
    ipfs_uri_to_bytes32,
    ERC8004Client,
    Web3Adapter,
)
from web3 import Web3
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Contract addresses
IDENTITY_REGISTRY = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
REPUTATION_REGISTRY = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
VALIDATION_REGISTRY = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"

# Example agent registration data
agent_data = {
    "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
    "name": "My AI Agent",
    "description": "An autonomous agent for task automation",
    "image": "https://example.com/agent-avatar.png",
    "endpoints": [
        {
            "name": "A2A",
            "endpoint": "https://agent.example.com/.well-known/agent-card.json",
            "version": "0.3.0",
        },
        {
            "name": "agentWallet",
            "endpoint": "eip155:31337:0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb7",
        },
    ],
    "registrations": [],
    "supportedTrust": ["reputation", "crypto-economic"],
}


def main():
    print("🚀 IPFS Upload & Pinning Example\n")

    # ============================================
    # 1. Setup IPFS Client
    # ============================================

    # Option 1: Using Pinata (recommended for production)
    pinata_key = os.getenv("PINATA_API_KEY")
    pinata_secret = os.getenv("PINATA_API_SECRET")

    if not pinata_key or not pinata_secret:
        print("⚠️  Pinata credentials not found in environment variables")
        print("   Set PINATA_API_KEY and PINATA_API_SECRET to run this example")
        return

    pinata_config = IPFSClientConfig(
        provider="pinata",
        api_key=pinata_key,
        api_secret=pinata_secret,
        gateway_url="https://gateway.pinata.cloud/ipfs/",  # Optional custom gateway
    )

    # Option 2: Using NFT.Storage
    # nft_storage_config = IPFSClientConfig(
    #     provider="nftstorage",
    #     api_key=os.getenv("NFT_STORAGE_KEY", "your-nft-storage-key"),
    #     gateway_url="https://nftstorage.link/ipfs/",
    # )

    # Option 3: Using Web3.Storage
    # web3_storage_config = IPFSClientConfig(
    #     provider="web3storage",
    #     api_key=os.getenv("WEB3_STORAGE_KEY", "your-web3-storage-key"),
    # )

    # Option 4: Using local IPFS node
    # local_ipfs_config = IPFSClientConfig(
    #     provider="ipfs",
    #     node_url="http://127.0.0.1:5001",  # Your local IPFS daemon
    #     gateway_url="http://127.0.0.1:8080/ipfs/",
    # )

    # Create client (using Pinata for this example)
    ipfs = create_ipfs_client(pinata_config)

    # ============================================
    # 2. Upload JSON Data (Agent Registration)
    # ============================================

    print("📤 Uploading agent registration data to IPFS...")
    try:
        result = ipfs.upload_json(
            agent_data,
            name="my-agent-registration.json",
            metadata={"project": "erc-8004-py", "type": "agent-registration"},
        )

        print("✅ Upload successful!")
        print(f"   CID: {result.cid}")
        print(f"   URI: {result.uri}")
        print(f"   Gateway URL: {result.url}")
        if result.size:
            print(f"   Size: {result.size} bytes")
        print()

        # ============================================
        # 3. Fetch Content from IPFS
        # ============================================

        print("📥 Fetching content from IPFS...")
        fetched_data = ipfs.fetch_json(result.cid)
        print(f"✅ Fetched agent name: {fetched_data['name']}")
        print()

        # ============================================
        # 4. Pin Content (keep it available)
        # ============================================

        print("📌 Pinning content to ensure availability...")
        ipfs.pin(result.cid, name="my-agent-registration")
        print("✅ Content pinned successfully!")
        print()

        # ============================================
        # 5. Register Agent with IPFS URI
        # ============================================

        print("📝 Registering agent with IPFS URI...")

        # Setup blockchain connection (local Hardhat)
        provider_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
        private_key = os.getenv(
            "PRIVATE_KEY",
            "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",  # Hardhat default account
        )

        w3 = Web3(Web3.HTTPProvider(provider_url))

        if not w3.is_connected():
            print("⚠️  Could not connect to local blockchain")
            print("   Make sure Hardhat node is running: npx hardhat node")
            print("   Skipping blockchain registration...\n")
        else:
            adapter = Web3Adapter(w3, private_key=private_key)
            client = ERC8004Client(
                adapter=adapter,
                addresses={
                    "identityRegistry": IDENTITY_REGISTRY,
                    "reputationRegistry": REPUTATION_REGISTRY,
                    "validationRegistry": VALIDATION_REGISTRY,
                    "chainId": 31337,  # Hardhat chain ID
                },
            )

            # Register agent with IPFS URI
            registration = client.identity.register_with_uri(result.uri)
            print("✅ Agent registered!")
            print(f"   Agent ID: {registration['agentId']}")
            print(f"   Transaction: {registration['txHash']}")
            print()

            # ============================================
            # 6. Fetch Agent from Registry & Parse IPFS Data
            # ============================================

            print("🔍 Fetching agent from registry...")

            # Get the agent's token URI from the registry
            agent_uri = client.identity.get_token_uri(registration["agentId"])
            print(f"✅ Retrieved agent URI: {agent_uri}")

            # Fetch and parse the IPFS data
            print("📥 Fetching agent data from IPFS...")
            agent_data_from_ipfs = ipfs.fetch_json(agent_uri)

            print("✅ Agent data retrieved and parsed:")
            print(f"   Name: {agent_data_from_ipfs['name']}")
            print(f"   Description: {agent_data_from_ipfs['description']}")
            print(f"   Type: {agent_data_from_ipfs['type']}")
            print(f"   Endpoints: {len(agent_data_from_ipfs['endpoints'])}")
            print(f"   Supported Trust: {agent_data_from_ipfs['supportedTrust']}")

            # Validate the structure matches ERC-8004 spec
            if agent_data_from_ipfs["type"] != "https://eips.ethereum.org/EIPS/eip-8004#registration-v1":
                print("⚠️  Warning: Agent registration type does not match ERC-8004 spec")

            # Example: Access specific endpoints
            a2a_endpoint = next(
                (ep for ep in agent_data_from_ipfs["endpoints"] if ep["name"] == "A2A"),
                None,
            )
            if a2a_endpoint:
                print(f"   A2A Endpoint: {a2a_endpoint['endpoint']}")
            print()

            # ============================================
            # 7. Upload Feedback/Validation Data
            # ============================================

            feedback_data = {
                "task": "Data analysis task #123",
                "performance": {
                    "accuracy": 0.95,
                    "latency_ms": 1500,
                    "completeness": 1.0,
                },
                "comments": "Excellent work, met all requirements",
                "timestamp": "2025-10-15T00:00:00Z",
            }

            print("📤 Uploading feedback data to IPFS...")
            feedback_result = ipfs.upload_json(feedback_data, name="feedback-123.json")
            print(f"✅ Feedback uploaded: {feedback_result.uri}")
            print()

            # Now you can use this URI when submitting feedback
            # feedback_hash = ipfs_uri_to_bytes32(feedback_result.uri)
            # await client.reputation.give_feedback(
            #     agent_id=registration["agentId"],
            #     score=95,
            #     tag1="excellent",
            #     tag2="reliable",
            #     feedback_auth=signed_auth,
            # )

    except Exception as error:
        print(f"❌ Error: {error}")


# ============================================
# Advanced Examples
# ============================================


def complete_agent_lifecycle():
    """
    Example: Complete Agent Lifecycle - Upload, Register, Fetch, Verify
    This shows the full cycle of agent registration and data retrieval
    """
    print("\n🔄 Complete Agent Lifecycle Example\n")

    # 1. Create IPFS client
    ipfs = create_ipfs_client(
        IPFSClientConfig(
            provider="pinata",
            api_key=os.getenv("PINATA_API_KEY", ""),
            api_secret=os.getenv("PINATA_API_SECRET", ""),
        )
    )

    # 2. Prepare agent metadata
    agent_metadata = {
        "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
        "name": "Advanced Analytics Agent",
        "description": "Specialized in data analysis and insights",
        "image": "https://example.com/analytics-agent.png",
        "endpoints": [
            {
                "name": "A2A",
                "endpoint": "https://analytics.example.com/.well-known/agent-card.json",
                "version": "0.3.0",
            }
        ],
        "registrations": [],
        "supportedTrust": ["reputation", "validation"],
    }

    # 3. Upload to IPFS
    print("📤 Step 1: Uploading agent metadata to IPFS...")
    upload_result = ipfs.upload_json(agent_metadata, name="analytics-agent.json")
    print(f"   ✅ Uploaded with CID: {upload_result.cid}")

    # 4. Register on blockchain
    print("📝 Step 2: Registering agent on blockchain...")
    provider_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
    private_key = os.getenv(
        "PRIVATE_KEY",
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    )

    w3 = Web3(Web3.HTTPProvider(provider_url))

    if not w3.is_connected():
        print("   ⚠️  Could not connect to blockchain")
        return

    adapter = Web3Adapter(w3, private_key=private_key)
    client = ERC8004Client(
        adapter=adapter,
        addresses={
            "identityRegistry": IDENTITY_REGISTRY,
            "reputationRegistry": REPUTATION_REGISTRY,
            "validationRegistry": VALIDATION_REGISTRY,
            "chainId": 31337,
        },
    )

    registration = client.identity.register_with_uri(upload_result.uri)
    print(f"   ✅ Registered as Agent ID: {registration['agentId']}")

    # 5. Fetch from registry (simulating another user discovering the agent)
    print("🔍 Step 3: Fetching agent data from registry...")
    registered_uri = client.identity.get_token_uri(registration["agentId"])
    print(f"   ✅ Retrieved URI: {registered_uri}")

    # 6. Fetch and parse IPFS data
    print("📥 Step 4: Fetching agent metadata from IPFS...")
    retrieved_metadata = ipfs.fetch_json(registered_uri)
    print(f"   ✅ Retrieved agent: {retrieved_metadata['name']}")

    # 7. Verify integrity
    print("🔐 Step 5: Verifying data integrity...")
    original_json = json.dumps(agent_metadata, sort_keys=True)
    retrieved_json = json.dumps(retrieved_metadata, sort_keys=True)
    integrity_match = original_json == retrieved_json
    print(f"   {'✅' if integrity_match else '❌'} Data integrity: {'VERIFIED' if integrity_match else 'FAILED'}")

    # 8. Parse and use agent data
    print("📊 Step 6: Using agent data...")
    print(f"   Agent supports: {', '.join(retrieved_metadata['supportedTrust'])}")
    print(f"   Endpoints available: {len(retrieved_metadata['endpoints'])}")

    return {
        "agent_id": registration["agentId"],
        "cid": upload_result.cid,
        "metadata": retrieved_metadata,
    }


def discover_agent(agent_id: int):
    """
    Example: Discover and interact with an existing agent
    """
    print(f"\n🔎 Discovering Agent ID: {agent_id}\n")

    # Setup clients
    ipfs = create_ipfs_client(
        IPFSClientConfig(
            provider="pinata",
            api_key=os.getenv("PINATA_API_KEY", ""),
            api_secret=os.getenv("PINATA_API_SECRET", ""),
        )
    )

    provider_url = os.getenv("RPC_URL", "http://127.0.0.1:8545")
    private_key = os.getenv(
        "PRIVATE_KEY",
        "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    )

    w3 = Web3(Web3.HTTPProvider(provider_url))

    if not w3.is_connected():
        print("❌ Could not connect to blockchain")
        return

    adapter = Web3Adapter(w3, private_key=private_key)
    client = ERC8004Client(
        adapter=adapter,
        addresses={
            "identityRegistry": IDENTITY_REGISTRY,
            "reputationRegistry": REPUTATION_REGISTRY,
            "validationRegistry": VALIDATION_REGISTRY,
            "chainId": 31337,
        },
    )

    # 1. Fetch agent URI from registry
    print("📖 Fetching agent from registry...")
    uri = client.identity.get_token_uri(agent_id)
    print(f"   Token URI: {uri}")

    # 2. Fetch agent data from IPFS
    print("📥 Fetching agent data from IPFS...")
    agent_data = ipfs.fetch_json(uri)

    # 3. Display agent information
    print("\n📋 Agent Information:")
    print(f"   Name: {agent_data['name']}")
    print(f"   Description: {agent_data['description']}")
    print(f"   Type: {agent_data['type']}")

    # 4. Check trust models
    print("\n🔒 Trust Models:")
    if agent_data.get("supportedTrust") and len(agent_data["supportedTrust"]) > 0:
        for trust in agent_data["supportedTrust"]:
            print(f"   ✓ {trust}")
    else:
        print("   ⚠️  No trust models specified")

    # 5. List endpoints
    print("\n🔌 Endpoints:")
    if agent_data.get("endpoints") and len(agent_data["endpoints"]) > 0:
        for endpoint in agent_data["endpoints"]:
            print(f"   • {endpoint['name']}: {endpoint['endpoint']}")
            if endpoint.get("version"):
                print(f"     Version: {endpoint['version']}")
    else:
        print("   ⚠️  No endpoints defined")

    # 6. Check registrations
    print("\n📝 Registrations:")
    if agent_data.get("registrations") and len(agent_data["registrations"]) > 0:
        for reg in agent_data["registrations"]:
            print(f"   • Agent ID: {reg['agentId']} on {reg['agentRegistry']}")
    else:
        print("   No cross-chain registrations")

    return agent_data


def upload_file_buffer():
    """
    Example: Upload a file buffer
    """
    ipfs = create_ipfs_client(
        IPFSClientConfig(
            provider="pinata",
            api_key=os.getenv("PINATA_API_KEY", ""),
            api_secret=os.getenv("PINATA_API_SECRET", ""),
        )
    )

    # Upload binary data
    buffer = b"Hello, IPFS!"
    result = ipfs.upload(buffer, name="message.txt")

    print(f"Uploaded buffer: {result.uri}")
    return result


def upload_with_manifest():
    """
    Example: Upload multiple files and create a manifest
    """
    ipfs = create_ipfs_client(
        IPFSClientConfig(
            provider="nftstorage",
            api_key=os.getenv("NFT_STORAGE_KEY", ""),
        )
    )

    # Upload individual files
    file1 = ipfs.upload_json({"data": "File 1"})
    file2 = ipfs.upload_json({"data": "File 2"})

    # Create manifest
    manifest = {
        "files": [
            {"name": "file1.json", "uri": file1.uri},
            {"name": "file2.json", "uri": file2.uri},
        ]
    }

    manifest_result = ipfs.upload_json(manifest, name="manifest.json")

    print(f"Manifest CID: {manifest_result.cid}")
    return manifest_result


def bulk_upload(data_array: list):
    """
    Example: Bulk upload with error handling
    """
    ipfs = create_ipfs_client(
        IPFSClientConfig(
            provider="web3storage",
            api_key=os.getenv("WEB3_STORAGE_KEY", ""),
        )
    )

    results = []

    for index, data in enumerate(data_array):
        try:
            result = ipfs.upload_json(data, name=f"data-{index}.json")
            results.append({"success": True, "result": result})
            print(f"✅ Uploaded {index + 1}/{len(data_array)}")
        except Exception as error:
            results.append({"success": False, "error": str(error)})
            print(f"❌ Failed {index + 1}/{len(data_array)}")

    return results


if __name__ == "__main__":
    main()

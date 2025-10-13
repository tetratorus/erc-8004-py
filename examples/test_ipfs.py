"""
Example script to test IPFS functionality

This example demonstrates:
- Uploading JSON data to IPFS
- Fetching content from IPFS
- Converting CIDs to bytes32
- Using different IPFS providers
"""

import os

from dotenv import load_dotenv

from erc8004 import IPFSClientConfig, cid_to_bytes32, create_ipfs_client, ipfs_uri_to_bytes32

# Load environment variables
load_dotenv()


def main():
    print("🚀 ERC-8004 IPFS Test\n")

    # Test 1: CID conversion utilities
    print("📋 Test 1: CID to bytes32 conversion")
    try:
        test_cid = "QmR7GSQM93Cx5eAg6a6yRzNde1FQv7uL6X1o4k7zrJa3LX"
        bytes32_hash = cid_to_bytes32(test_cid)
        print(f"✅ CID: {test_cid}")
        print(f"   Bytes32: {bytes32_hash}\n")

        test_uri = f"ipfs://{test_cid}"
        bytes32_from_uri = ipfs_uri_to_bytes32(test_uri)
        print(f"✅ URI: {test_uri}")
        print(f"   Bytes32: {bytes32_from_uri}\n")

        assert bytes32_hash == bytes32_from_uri, "Conversion mismatch!"
        print("✅ Conversions match!\n")
    except Exception as error:
        print(f"❌ Error: {error}\n")

    # Test 2: Upload JSON to IPFS (using Pinata as example)
    print("📋 Test 2: Upload JSON to IPFS")

    # Check if Pinata credentials are available
    pinata_key = os.getenv("PINATA_API_KEY")
    pinata_secret = os.getenv("PINATA_API_SECRET")

    if not pinata_key or not pinata_secret:
        print("⚠️  Pinata credentials not found in environment variables")
        print("   Set PINATA_API_KEY and PINATA_API_SECRET to test uploads")
        print("   For now, we'll demonstrate with fetch only\n")
    else:
        try:
            # Create IPFS client
            config = IPFSClientConfig(
                provider="pinata",
                api_key=pinata_key,
                api_secret=pinata_secret,
            )
            ipfs = create_ipfs_client(config)

            # Upload agent registration data
            agent_data = {
                "type": "https://eips.ethereum.org/EIPS/eip-8004#registration-v1",
                "name": "Python Test Agent",
                "description": "An agent registered using the Python SDK",
                "image": "https://example.com/agent.png",
                "endpoints": [
                    {
                        "name": "A2A",
                        "endpoint": "https://agent.example/.well-known/agent-card.json",
                        "version": "0.3.0",
                    }
                ],
                "supportedTrust": ["reputation", "validation"],
            }

            result = ipfs.upload_json(agent_data, name="test-agent.json")
            print("✅ Uploaded to IPFS!")
            print(f"   CID: {result.cid}")
            print(f"   URI: {result.uri}")
            print(f"   URL: {result.url}")
            if result.size:
                print(f"   Size: {result.size} bytes\n")

            # Convert CID to bytes32 for on-chain use
            request_hash = cid_to_bytes32(result.cid)
            print(f"✅ Request hash for validation: {request_hash}\n")

        except Exception as error:
            print(f"❌ Error uploading: {error}\n")

    # Test 3: Fetch from IPFS
    print("📋 Test 3: Fetch content from IPFS")
    try:
        # Use a known public CID for testing
        # This is a test file - replace with your own CID
        print("   Fetching from public IPFS gateway...")
        print("   (This may take a moment...)\n")

        # Create a read-only IPFS client (no credentials needed for fetching)
        config = IPFSClientConfig(provider="ipfs", gateway_url="https://ipfs.io/ipfs/")
        ipfs = create_ipfs_client(config)

        # Try to fetch a well-known IPFS file (IPFS docs logo)
        test_cid = "QmPZ9gcCEpqKTo6aq61g2nXGUhM4iCL3ewB6LDXZCtioEB"
        try:
            print(f"   Attempting to fetch CID: {test_cid}")
            # Note: This is a text file, so it should work
            # For binary files, you'd need to handle the response differently
            content = ipfs.fetch(test_cid)
            print(f"✅ Fetched content ({len(content)} bytes)")
            print(f"   Preview: {content[:100]}...\n")
        except Exception as fetch_error:
            print(f"⚠️  Fetch failed (gateway may be slow): {fetch_error}")
            print("   This is normal - public IPFS gateways can be unreliable\n")

    except Exception as error:
        print(f"❌ Error: {error}\n")

    # Test 4: Get gateway URL
    print("📋 Test 4: Gateway URL generation")
    try:
        config = IPFSClientConfig(provider="ipfs")
        ipfs = create_ipfs_client(config)

        test_cid = "QmExample123"
        gateway_url = ipfs.get_gateway_url(test_cid)
        print(f"✅ Gateway URL: {gateway_url}\n")
    except Exception as error:
        print(f"❌ Error: {error}\n")

    print("✨ All IPFS tests completed!")
    print("\n💡 Tips:")
    print("   - Set up Pinata, NFT.Storage, or Web3.Storage for reliable uploads")
    print("   - Use IPFS URIs in agent registration for decentralized storage")
    print("   - Convert CIDs to bytes32 for validation request hashes")


if __name__ == "__main__":
    main()

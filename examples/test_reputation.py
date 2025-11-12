"""
Example script to test ERC-8004 Reputation/Feedback functionality

Prerequisites:
1. Run hardhat node: npx hardhat node
2. Deploy contracts with the ignition script

This example demonstrates:
- Registering an agent
- Creating and signing feedbackAuth
- Submitting feedback
- Reading feedback and reputation summaries
"""

import time

from erc8004 import ERC8004Client, Web3Adapter
from web3 import Web3

# Contract addresses - CREATE2 vanity addresses (same on all networks)
IDENTITY_REGISTRY = "0x8004AbdDA9b877187bF865eD1d8B5A41Da3c4997"
REPUTATION_REGISTRY = "0x8004B312333aCb5764597c2BeEe256596B5C6876"
VALIDATION_REGISTRY = "0x8004C8AEF64521bC97AB50799d394CDb785885E3"


def main():
    print("🚀 ERC-8004 Reputation/Feedback Test\n")

    # Connect to local Hardhat
    print("Connecting to local Hardhat...")
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

    # Use first account as agent owner (hardhat account 0)
    agent_owner_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    # Use second account as client (hardhat account 1)
    client_key = "0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d"

    agent_adapter = Web3Adapter(w3, private_key=agent_owner_key)
    client_adapter = Web3Adapter(w3, private_key=client_key)

    agent_owner_address = agent_adapter.get_address()
    client_address = client_adapter.get_address()

    print(f"Agent Owner: {agent_owner_address}")
    print(f"Client: {client_address}\n")

    # Create SDK instance for agent owner
    agent_sdk = ERC8004Client(
        adapter=agent_adapter,
        addresses={
            "identityRegistry": IDENTITY_REGISTRY,
            "reputationRegistry": REPUTATION_REGISTRY,
            "validationRegistry": VALIDATION_REGISTRY,
            "chainId": 31337,
        },
    )

    # Create SDK instance for client
    client_sdk = ERC8004Client(
        adapter=client_adapter,
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

    # Step 2: Client submits feedback (NO feedbackAuth needed in new contract!)
    print("📋 Step 2: Client submitting feedback...")
    feedback_result = client_sdk.reputation.give_feedback(
        agent_id=agent_id,
        score=95,
        tag1="excellent",
        tag2="fast",
    )
    print("✅ Feedback submitted!")
    print("   Score: 95 / 100")
    print("   Tags: excellent, fast")
    print(f"   TX Hash: {feedback_result['txHash']}\n")

    # Step 3: Read the feedback back
    print("\n📋 Step 3: Reading feedback...")
    feedback = client_sdk.reputation.read_feedback(agent_id, client_address, 1)
    print("✅ Feedback retrieved:")
    print(f"   Score: {feedback['score']} / 100")
    print(f"   Tag1: {feedback['tag1']}")
    print(f"   Tag2: {feedback['tag2']}")
    print(f"   Revoked: {feedback['isRevoked']}\n")

    # Step 4: Get reputation summary
    print("📋 Step 4: Getting reputation summary...")
    summary = client_sdk.reputation.get_summary(agent_id, [client_address])
    print("✅ Reputation summary:")
    print(f"   Feedback Count: {summary['count']}")
    print(f"   Average Score: {summary['averageScore']} / 100\n")

    # Step 5: Get all clients who gave feedback
    print("📋 Step 5: Getting all clients...")
    clients = client_sdk.reputation.get_clients(agent_id)
    print(f"✅ Clients who gave feedback: {len(clients)}")
    print(f"   {', '.join(clients)}\n")

    # Step 6: Submit another feedback with higher score
    print("📋 Step 6: Submitting second feedback...")
    client_sdk.reputation.give_feedback(
        agent_id=agent_id, score=98
    )
    print("✅ Second feedback submitted (score: 98)\n")

    # Step 7: Get updated summary
    print("📋 Step 7: Getting updated reputation summary...")
    updated_summary = client_sdk.reputation.get_summary(agent_id)
    print("✅ Updated reputation summary:")
    print(f"   Feedback Count: {updated_summary['count']}")
    print(f"   Average Score: {updated_summary['averageScore']} / 100\n")

    # Step 8: Read all feedback
    print("\n📋 Step 8: Reading all feedback...")
    all_feedback = client_sdk.reputation.read_all_feedback(agent_id)
    print("✅ All feedback retrieved:")
    print(f"   Total: {len(all_feedback['scores'])} feedback entries")
    for i, score in enumerate(all_feedback["scores"]):
        print(f"   [{i}] Client: {all_feedback['clientAddresses'][i][:10]}... Score: {score}")

    # Step 9: Revoke the first feedback
    print("\n📋 Step 9: Revoking first feedback...")
    revoke_result = client_sdk.reputation.revoke_feedback(agent_id, 1)
    print("✅ Feedback revoked!")
    print(f"   TX Hash: {revoke_result['txHash']}\n")

    # Step 10: Verify feedback is revoked
    print("📋 Step 10: Verifying revoked feedback...")
    revoked_feedback = client_sdk.reputation.read_feedback(agent_id, client_address, 1)
    print("✅ Revoked feedback status:")
    print(f"   Score: {revoked_feedback['score']} / 100")
    print(f"   Revoked: {revoked_feedback['isRevoked']}\n")

    # Step 11: Get summary after revoke (should exclude revoked feedback)
    print("📋 Step 11: Getting summary after revoke...")
    final_summary = client_sdk.reputation.get_summary(agent_id)
    print("✅ Final reputation summary (excluding revoked):")
    print(f"   Feedback Count: {final_summary['count']}")
    print(f"   Average Score: {final_summary['averageScore']} / 100\n")

    print("🎉 All tests completed successfully!")


if __name__ == "__main__":
    main()

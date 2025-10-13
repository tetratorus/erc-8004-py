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

# Contract addresses from your deployment
IDENTITY_REGISTRY = "0x5FbDB2315678afecb367f032d93F642f64180aa3"
REPUTATION_REGISTRY = "0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
VALIDATION_REGISTRY = "0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"


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

    # Step 2: Get chain ID and create feedbackAuth
    print("📋 Step 2: Creating feedbackAuth...")
    chain_id = agent_sdk.get_chain_id()

    # Get the last feedback index for this client
    last_index = agent_sdk.reputation.get_last_index(agent_id, client_address)
    print(f"   Last feedback index: {last_index}")

    # Create feedbackAuth
    feedback_auth = agent_sdk.reputation.create_feedback_auth(
        agent_id,
        client_address,
        last_index + 1,  # Allow next feedback
        int(time.time()) + 3600,  # Valid for 1 hour
        chain_id,
        agent_owner_address,
    )
    print("✅ FeedbackAuth created")
    print(f"   indexLimit: {feedback_auth['indexLimit']}")
    print(f"   expiry: {feedback_auth['expiry']}\n")

    # Step 3: Agent owner signs the feedbackAuth
    print("📋 Step 3: Signing feedbackAuth...")
    signed_auth = agent_sdk.reputation.sign_feedback_auth(feedback_auth)
    print("✅ FeedbackAuth signed")
    print(f"   Signature length: {len(signed_auth)}")
    print(f"   Signature: {signed_auth[:20]}...\n")

    # Step 4: Client submits feedback
    print("📋 Step 4: Client submitting feedback...")
    feedback_result = client_sdk.reputation.give_feedback(
        agent_id=agent_id,
        score=95,
        feedback_auth=signed_auth,
        tag1="excellent",
        tag2="fast",
    )
    print("✅ Feedback submitted!")
    print("   Score: 95 / 100")
    print("   Tags: excellent, fast")
    print(f"   TX Hash: {feedback_result['txHash']}\n")

    # Step 5: Read the feedback back
    print("📋 Step 5: Reading feedback...")
    feedback = client_sdk.reputation.read_feedback(agent_id, client_address, 1)
    print("✅ Feedback retrieved:")
    print(f"   Score: {feedback['score']} / 100")
    print(f"   Tag1: {feedback['tag1']}")
    print(f"   Tag2: {feedback['tag2']}")
    print(f"   Revoked: {feedback['isRevoked']}\n")

    # Step 6: Get reputation summary
    print("📋 Step 6: Getting reputation summary...")
    summary = client_sdk.reputation.get_summary(agent_id, [client_address])
    print("✅ Reputation summary:")
    print(f"   Feedback Count: {summary['count']}")
    print(f"   Average Score: {summary['averageScore']} / 100\n")

    # Step 7: Get all clients who gave feedback
    print("📋 Step 7: Getting all clients...")
    clients = client_sdk.reputation.get_clients(agent_id)
    print(f"✅ Clients who gave feedback: {len(clients)}")
    print(f"   {', '.join(clients)}\n")

    # Step 8: Submit another feedback with higher score
    print("📋 Step 8: Submitting second feedback...")
    new_last_index = agent_sdk.reputation.get_last_index(agent_id, client_address)
    feedback_auth2 = agent_sdk.reputation.create_feedback_auth(
        agent_id,
        client_address,
        new_last_index + 1,
        int(time.time()) + 3600,
        chain_id,
        agent_owner_address,
    )
    signed_auth2 = agent_sdk.reputation.sign_feedback_auth(feedback_auth2)

    client_sdk.reputation.give_feedback(
        agent_id=agent_id, score=98, feedback_auth=signed_auth2
    )
    print("✅ Second feedback submitted (score: 98)\n")

    # Step 9: Get updated summary
    print("📋 Step 9: Getting updated reputation summary...")
    updated_summary = client_sdk.reputation.get_summary(agent_id)
    print("✅ Updated reputation summary:")
    print(f"   Feedback Count: {updated_summary['count']}")
    print(f"   Average Score: {updated_summary['averageScore']} / 100\n")

    # Step 10: Read all feedback
    print("📋 Step 10: Reading all feedback...")
    all_feedback = client_sdk.reputation.read_all_feedback(agent_id)
    print("✅ All feedback retrieved:")
    print(f"   Total: {len(all_feedback['scores'])} feedback entries")
    for i, score in enumerate(all_feedback["scores"]):
        print(f"   [{i}] Client: {all_feedback['clientAddresses'][i][:10]}... Score: {score}")

    print("\n🎉 All tests completed successfully!")


if __name__ == "__main__":
    main()

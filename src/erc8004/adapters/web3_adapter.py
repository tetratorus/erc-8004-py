"""
Web3.py adapter implementation
"""

from typing import Any, Dict, List, Optional

from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3
from web3.contract import Contract
from web3.types import TxReceipt

from .base import BlockchainAdapter


class Web3Adapter(BlockchainAdapter):
    """
    Web3.py v6+ adapter implementation
    """

    def __init__(
        self,
        web3: Web3,
        account: Optional[Account] = None,
        private_key: Optional[str] = None,
    ):
        """
        Initialize Web3 adapter

        Args:
            web3: Web3 instance
            account: Account instance for signing (optional)
            private_key: Private key for signing (optional, will create account)
        """
        self.web3 = web3

        if private_key:
            self.account = Account.from_key(private_key)
        else:
            self.account = account

    def call(
        self,
        contract_address: str,
        abi: List[Dict[str, Any]],
        function_name: str,
        args: List[Any],
    ) -> Any:
        """Call a read-only contract function"""
        contract: Contract = self.web3.eth.contract(
            address=Web3.to_checksum_address(contract_address), abi=abi
        )
        function = getattr(contract.functions, function_name)
        return function(*args).call()

    def send(
        self,
        contract_address: str,
        abi: List[Dict[str, Any]],
        function_name: str,
        args: List[Any],
    ) -> Dict[str, Any]:
        """Send a transaction to a contract function"""
        if not self.account:
            raise ValueError("Account required for write operations")

        contract: Contract = self.web3.eth.contract(
            address=Web3.to_checksum_address(contract_address), abi=abi
        )

        # Build transaction
        function = getattr(contract.functions, function_name)
        transaction = function(*args).build_transaction(
            {
                "from": self.account.address,
                "nonce": self.web3.eth.get_transaction_count(self.account.address),
                "gas": 2000000,  # Adjust as needed
                "gasPrice": self.web3.eth.gas_price,
            }
        )

        # Sign transaction
        signed_txn = self.web3.eth.account.sign_transaction(
            transaction, private_key=self.account.key
        )

        # Send transaction (handle both raw_transaction and rawTransaction for compatibility)
        raw_tx = getattr(signed_txn, 'raw_transaction', None) or getattr(signed_txn, 'rawTransaction', None)
        tx_hash = self.web3.eth.send_raw_transaction(raw_tx)

        # Wait for receipt
        receipt: TxReceipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)

        # Parse events from receipt
        events = []
        for log in receipt["logs"]:
            try:
                # Try to decode each log with the contract ABI
                # Iterate through all events in the ABI to find a match
                for event_abi in [item for item in abi if item.get('type') == 'event']:
                    try:
                        event_signature = self.web3.keccak(text=f"{event_abi['name']}({','.join([input['type'] for input in event_abi['inputs']])})")
                        if log['topics'][0] == event_signature:
                            # Decode the event
                            decoded = contract.events[event_abi['name']]().process_log(log)
                            events.append(
                                {
                                    "name": decoded["event"],
                                    "args": dict(decoded["args"]),
                                }
                            )
                            break
                    except Exception:
                        continue
            except Exception:
                # Skip logs that don't match this contract's ABI
                pass

        return {
            "txHash": receipt["transactionHash"].hex(),
            "blockNumber": receipt["blockNumber"],
            "receipt": receipt,
            "events": events,
        }

    def get_address(self) -> Optional[str]:
        """Get the current signer/wallet address"""
        if not self.account:
            return None
        return self.account.address

    def get_chain_id(self) -> int:
        """Get the chain ID"""
        return self.web3.eth.chain_id

    def sign_message(self, message: bytes) -> str:
        """
        Sign a message (EIP-191)

        Args:
            message: Message bytes to sign

        Returns:
            Signature as hex string
        """
        if not self.account:
            raise ValueError("Account required for signing")

        # Encode message with EIP-191 prefix
        signable_message = encode_defunct(primitive=message)
        signed_message = self.web3.eth.account.sign_message(
            signable_message, private_key=self.account.key
        )

        return signed_message.signature.hex()

    def sign_typed_data(
        self, domain: Dict[str, Any], types: Dict[str, Any], value: Dict[str, Any]
    ) -> str:
        """
        Sign typed data (EIP-712)

        Args:
            domain: EIP-712 domain
            types: EIP-712 types
            value: Message value

        Returns:
            Signature as hex string
        """
        if not self.account:
            raise ValueError("Account required for signing")

        # Construct EIP-712 structured data
        structured_data = {
            "types": types,
            "primaryType": list(types.keys())[0],
            "domain": domain,
            "message": value,
        }

        # Use Account.sign_typed_data directly (newer eth-account API)
        signed_message = Account.sign_typed_data(
            structured_data, private_key=self.account.key
        )

        return signed_message.signature.hex()

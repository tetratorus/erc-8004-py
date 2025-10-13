"""
IPFS Client Configuration and Utilities
"""

import json
from typing import Any, Dict, List, Optional, Union

import requests


class IPFSClientConfig:
    """Configuration for IPFS client"""

    def __init__(
        self,
        provider: str,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        gateway_url: Optional[str] = None,
        node_url: Optional[str] = None,
    ):
        """
        Initialize IPFS client configuration

        Args:
            provider: Service provider ('pinata', 'nftstorage', 'web3storage', 'ipfs')
            api_key: API key/token for the service
            api_secret: API secret (required for Pinata)
            gateway_url: Custom IPFS gateway URL
            node_url: Custom IPFS node URL (for local IPFS)
        """
        self.provider = provider
        self.api_key = api_key
        self.api_secret = api_secret
        self.gateway_url = gateway_url or "https://ipfs.io/ipfs/"
        self.node_url = node_url or "http://127.0.0.1:5001"


class IPFSUploadResult:
    """Result from IPFS upload"""

    def __init__(self, cid: str, uri: str, url: str, size: Optional[int] = None):
        """
        Initialize upload result

        Args:
            cid: The IPFS CID (Content Identifier)
            uri: Full IPFS URI (ipfs://...)
            url: Gateway URL for accessing the content
            size: File size in bytes (optional)
        """
        self.cid = cid
        self.uri = uri
        self.url = url
        self.size = size

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {"cid": self.cid, "uri": self.uri, "url": self.url}
        if self.size is not None:
            result["size"] = self.size
        return result


# Base58 alphabet (Bitcoin style)
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def base58_decode(input_str: str) -> bytes:
    """
    Decode a base58 string to bytes

    Args:
        input_str: Base58 encoded string

    Returns:
        Decoded bytes

    Raises:
        ValueError: If invalid base58 character encountered
    """
    bytes_list: List[int] = []

    for char in input_str:
        carry = BASE58_ALPHABET.index(char)
        if carry < 0:
            raise ValueError(f"Invalid base58 character: {char}")

        for j in range(len(bytes_list)):
            carry += bytes_list[j] * 58
            bytes_list[j] = carry & 0xFF
            carry >>= 8

        while carry > 0:
            bytes_list.append(carry & 0xFF)
            carry >>= 8

    # Handle leading zeros
    for char in input_str:
        if char != "1":
            break
        bytes_list.append(0)

    return bytes(reversed(bytes_list))


def cid_to_bytes32(cid_str: str) -> str:
    """
    Convert any IPFS CID (v0) to bytes32 hex string
    Works for Qm... (CIDv0) formats

    Args:
        cid_str: The IPFS CID string (v0 like "QmXXX...")

    Returns:
        Ethereum bytes32 hex string (0x-prefixed)

    Raises:
        ValueError: If the CID is invalid or digest length is not 32 bytes

    Example:
        >>> cid_v0 = 'QmR7GSQM93Cx5eAg6a6yRzNde1FQv7uL6X1o4k7zrJa3LX'
        >>> bytes32 = cid_to_bytes32(cid_v0)
        # Returns: '0x...' (32 bytes hex)
    """
    # CIDv0 always starts with 'Qm'
    if not cid_str.startswith("Qm"):
        raise ValueError("Only CIDv0 (starting with Qm) is currently supported")

    # Decode base58
    decoded_bytes = base58_decode(cid_str)

    # CIDv0 format: [0x12, 0x20, ...32 bytes of hash...]
    # 0x12 = sha256 hash function code
    # 0x20 = 32 bytes length
    if len(decoded_bytes) != 34:
        raise ValueError(
            f"Invalid CID length: {len(decoded_bytes)}, expected 34"
        )

    if decoded_bytes[0] != 0x12 or decoded_bytes[1] != 0x20:
        raise ValueError("Invalid CID format: expected SHA-256 hash")

    # Extract the 32-byte hash (skip the 2-byte header)
    hash_bytes = decoded_bytes[2:]

    # Convert to hex string
    return "0x" + hash_bytes.hex()


def ipfs_uri_to_bytes32(uri: str) -> str:
    """
    Extract CID from IPFS URI and convert to bytes32
    Handles both raw CIDs and ipfs:// URIs

    Args:
        uri: IPFS URI (e.g., "ipfs://QmXXX..." or just "QmXXX...")

    Returns:
        Ethereum bytes32 hex string (0x-prefixed)

    Example:
        >>> uri = 'ipfs://QmR7GSQM93Cx5eAg6a6yRzNde1FQv7uL6X1o4k7zrJa3LX'
        >>> bytes32 = ipfs_uri_to_bytes32(uri)
    """
    # Remove ipfs:// prefix if present
    cid = uri.replace("ipfs://", "")
    return cid_to_bytes32(cid)


class IPFSClient:
    """IPFS Client for uploading, pinning, and fetching content"""

    def __init__(self, config: IPFSClientConfig):
        """
        Initialize IPFS client

        Args:
            config: IPFS client configuration
        """
        self.config = config

    def upload(
        self,
        content: Union[str, bytes],
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> IPFSUploadResult:
        """
        Upload content to IPFS

        Args:
            content: String or bytes to upload
            name: Optional filename
            metadata: Optional metadata

        Returns:
            Upload result with CID and URLs
        """
        if self.config.provider == "pinata":
            return self._upload_to_pinata(content, name, metadata)
        elif self.config.provider == "nftstorage":
            return self._upload_to_nft_storage(content, name)
        elif self.config.provider == "web3storage":
            return self._upload_to_web3_storage(content, name)
        elif self.config.provider == "ipfs":
            return self._upload_to_local_ipfs(content, name)
        else:
            raise ValueError(f"Unsupported IPFS provider: {self.config.provider}")

    def upload_json(
        self, data: Any, name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None
    ) -> IPFSUploadResult:
        """
        Upload JSON data to IPFS

        Args:
            data: Python object to stringify and upload
            name: Optional filename
            metadata: Optional metadata

        Returns:
            Upload result
        """
        content = json.dumps(data, indent=2)
        filename = name or "data.json"
        return self.upload(content, filename, metadata)

    def pin(self, cid: str, name: Optional[str] = None) -> None:
        """
        Pin an existing CID (keep it available on the network)

        Args:
            cid: The CID to pin
            name: Optional name for the pin
        """
        if self.config.provider == "pinata":
            self._pin_on_pinata(cid, name)
        elif self.config.provider == "ipfs":
            self._pin_on_local_ipfs(cid)
        else:
            raise ValueError(f"Pinning not supported for provider: {self.config.provider}")

    def fetch(self, cid_or_uri: str) -> str:
        """
        Fetch content from IPFS

        Args:
            cid_or_uri: CID or ipfs:// URI

        Returns:
            Content as string
        """
        cid = cid_or_uri.replace("ipfs://", "")
        url = f"{self.config.gateway_url}{cid}"

        response = requests.get(url)
        response.raise_for_status()

        return response.text

    def fetch_json(self, cid_or_uri: str) -> Any:
        """
        Fetch JSON content from IPFS

        Args:
            cid_or_uri: CID or ipfs:// URI

        Returns:
            Parsed JSON object
        """
        content = self.fetch(cid_or_uri)
        return json.loads(content)

    def get_gateway_url(self, cid: str) -> str:
        """
        Get gateway URL for a CID

        Args:
            cid: The IPFS CID

        Returns:
            Full gateway URL
        """
        return f"{self.config.gateway_url}{cid}"

    # Private methods for different providers

    def _upload_to_pinata(
        self, content: Union[str, bytes], name: Optional[str], metadata: Optional[Dict[str, Any]]
    ) -> IPFSUploadResult:
        """Upload to Pinata"""
        if not self.config.api_key or not self.config.api_secret:
            raise ValueError("Pinata requires both api_key and api_secret")

        # Convert content to bytes if needed
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        # Create multipart form data
        files = {"file": (name or "file", content_bytes)}

        # Add metadata if provided
        data = {}
        if metadata or name:
            pinata_metadata = {}
            if name:
                pinata_metadata["name"] = name
            if metadata:
                pinata_metadata["keyvalues"] = metadata
            data["pinataMetadata"] = json.dumps(pinata_metadata)

        response = requests.post(
            "https://api.pinata.cloud/pinning/pinFileToIPFS",
            files=files,
            data=data,
            headers={
                "pinata_api_key": self.config.api_key,
                "pinata_secret_api_key": self.config.api_secret,
            },
        )
        response.raise_for_status()

        result = response.json()
        cid = result["IpfsHash"]

        return IPFSUploadResult(
            cid=cid,
            uri=f"ipfs://{cid}",
            url=self.get_gateway_url(cid),
            size=result.get("PinSize"),
        )

    def _upload_to_nft_storage(
        self, content: Union[str, bytes], name: Optional[str]
    ) -> IPFSUploadResult:
        """Upload to NFT.Storage"""
        if not self.config.api_key:
            raise ValueError("NFT.Storage requires an API key")

        # Convert content to bytes if needed
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        response = requests.post(
            "https://api.nft.storage/upload",
            data=content_bytes,
            headers={"Authorization": f"Bearer {self.config.api_key}"},
        )
        response.raise_for_status()

        result = response.json()
        cid = result["value"]["cid"]

        return IPFSUploadResult(
            cid=cid, uri=f"ipfs://{cid}", url=self.get_gateway_url(cid)
        )

    def _upload_to_web3_storage(
        self, content: Union[str, bytes], name: Optional[str]
    ) -> IPFSUploadResult:
        """Upload to Web3.Storage"""
        if not self.config.api_key:
            raise ValueError("Web3.Storage requires an API key")

        # Convert content to bytes if needed
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        files = {"file": (name or "file", content_bytes)}

        response = requests.post(
            "https://api.web3.storage/upload",
            files=files,
            headers={"Authorization": f"Bearer {self.config.api_key}"},
        )
        response.raise_for_status()

        result = response.json()
        cid = result["cid"]

        return IPFSUploadResult(
            cid=cid, uri=f"ipfs://{cid}", url=self.get_gateway_url(cid)
        )

    def _upload_to_local_ipfs(
        self, content: Union[str, bytes], name: Optional[str]
    ) -> IPFSUploadResult:
        """Upload to local IPFS node"""
        # Convert content to bytes if needed
        if isinstance(content, str):
            content_bytes = content.encode("utf-8")
        else:
            content_bytes = content

        files = {"file": (name or "file", content_bytes)}

        response = requests.post(f"{self.config.node_url}/api/v0/add", files=files)
        response.raise_for_status()

        result = response.json()
        cid = result["Hash"]

        return IPFSUploadResult(
            cid=cid,
            uri=f"ipfs://{cid}",
            url=self.get_gateway_url(cid),
            size=result.get("Size"),
        )

    def _pin_on_pinata(self, cid: str, name: Optional[str]) -> None:
        """Pin on Pinata"""
        if not self.config.api_key or not self.config.api_secret:
            raise ValueError("Pinata requires both api_key and api_secret")

        payload = {"hashToPin": cid}
        if name:
            payload["pinataMetadata"] = {"name": name}

        response = requests.post(
            "https://api.pinata.cloud/pinning/pinByHash",
            json=payload,
            headers={
                "Content-Type": "application/json",
                "pinata_api_key": self.config.api_key,
                "pinata_secret_api_key": self.config.api_secret,
            },
        )
        response.raise_for_status()

    def _pin_on_local_ipfs(self, cid: str) -> None:
        """Pin on local IPFS node"""
        response = requests.post(f"{self.config.node_url}/api/v0/pin/add?arg={cid}")
        response.raise_for_status()


def create_ipfs_client(config: IPFSClientConfig) -> IPFSClient:
    """
    Create an IPFS client instance

    Args:
        config: IPFS client configuration

    Returns:
        Configured IPFS client
    """
    return IPFSClient(config)

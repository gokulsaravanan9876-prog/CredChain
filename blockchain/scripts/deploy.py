"""
Compiles and deploys CredentialAnchor.sol to the network configured via
environment variables. Reads the same BLOCKCHAIN_* variables the backend
uses (see blockchain/README.md), so a successful deploy here is a successful
config for the backend too.

Usage:
    pip install web3 py-solc-x
    python blockchain/scripts/deploy.py

Requires (all via environment, or a .env file in this directory / the repo
root — see README):
    BLOCKCHAIN_RPC_URL
    BLOCKCHAIN_CHAIN_ID
    BLOCKCHAIN_PRIVATE_KEY   (must hold testnet gas funds)

Prints the deployed contract address and the ABI — copy the address into
backend/.env as BLOCKCHAIN_CONTRACT_ADDRESS. Never deploys to mainnet: this
script will refuse to run unless BLOCKCHAIN_CHAIN_ID matches a known
testnet id (Polygon Amoy = 80002) or BLOCKCHAIN_ALLOW_ANY_CHAIN=true is set
explicitly.
"""

import json
import os
import sys
from pathlib import Path

import solcx
from web3 import Web3

CONTRACT_PATH = Path(__file__).resolve().parent.parent / "contracts" / "CredentialAnchor.sol"
SOLC_VERSION = "0.8.24"
KNOWN_TESTNET_CHAIN_IDS = {80002}  # Polygon Amoy


def compile_contract() -> dict:
    solcx.install_solc(SOLC_VERSION)
    source = CONTRACT_PATH.read_text()
    compiled = solcx.compile_source(
        source,
        output_values=["abi", "bin"],
        solc_version=SOLC_VERSION,
    )
    contract_id, contract_interface = next(iter(compiled.items()))
    return contract_interface


def main() -> None:
    rpc_url = os.environ.get("BLOCKCHAIN_RPC_URL")
    chain_id_raw = os.environ.get("BLOCKCHAIN_CHAIN_ID")
    private_key = os.environ.get("BLOCKCHAIN_PRIVATE_KEY")
    allow_any_chain = os.environ.get("BLOCKCHAIN_ALLOW_ANY_CHAIN", "false").lower() == "true"

    if not rpc_url or not chain_id_raw or not private_key:
        print(
            "Missing BLOCKCHAIN_RPC_URL / BLOCKCHAIN_CHAIN_ID / BLOCKCHAIN_PRIVATE_KEY "
            "in the environment. See blockchain/README.md for how to configure a testnet."
        )
        sys.exit(1)

    chain_id = int(chain_id_raw)
    if chain_id not in KNOWN_TESTNET_CHAIN_IDS and not allow_any_chain:
        print(
            f"Refusing to deploy: chain id {chain_id} is not a recognized testnet "
            f"({KNOWN_TESTNET_CHAIN_IDS}). Set BLOCKCHAIN_ALLOW_ANY_CHAIN=true to override "
            "(never point this at mainnet)."
        )
        sys.exit(1)

    print(f"Compiling {CONTRACT_PATH.name} with solc {SOLC_VERSION}...")
    interface = compile_contract()
    abi = interface["abi"]
    bytecode = interface["bin"]

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        print(f"Could not connect to RPC at {rpc_url}")
        sys.exit(1)

    account = w3.eth.account.from_key(private_key)
    balance = w3.eth.get_balance(account.address)
    print(f"Deployer address: {account.address}")
    print(f"Balance: {w3.from_wei(balance, 'ether')} (native token)")
    if balance == 0:
        print("Deployer has zero balance — fund this address from a testnet faucet before deploying.")
        sys.exit(1)

    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(account.address)
    tx = Contract.constructor().build_transaction(
        {
            "chainId": chain_id,
            "from": account.address,
            "nonce": nonce,
        }
    )
    signed = w3.eth.account.sign_transaction(tx, private_key=private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f"Deployment tx sent: {tx_hash.hex()}")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Deployed at: {receipt.contractAddress}")
    print("\nSet this in backend/.env:")
    print(f"BLOCKCHAIN_CONTRACT_ADDRESS={receipt.contractAddress}")

    abi_path = Path(__file__).resolve().parent.parent / "contracts" / "CredentialAnchor.abi.json"
    abi_path.write_text(json.dumps(abi, indent=2))
    print(f"\nABI written to {abi_path}")


if __name__ == "__main__":
    main()

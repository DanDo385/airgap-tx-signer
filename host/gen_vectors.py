#!/usr/bin/env python3
"""Regenerate vectors/known_answers.json from eth_account (reference)."""
from __future__ import annotations

import json
from pathlib import Path

from eth_account import Account
from eth_account._utils.legacy_transactions import serializable_unsigned_transaction_from_dict
from eth_keys import keys
from eth_utils import keccak, to_checksum_address
from hexbytes import HexBytes

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "vectors" / "known_answers.json"

# THROW AWAY DEMO KEY ONLY.
PRIV_HEX = "0x0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"


def main() -> None:
    acct = Account.from_key(PRIV_HEX)
    pk = keys.PrivateKey(HexBytes(PRIV_HEX))
    pub_raw = pk.public_key.to_bytes()
    pub_unc = (b"\x04" + pub_raw) if len(pub_raw) == 64 else pub_raw
    assert to_checksum_address(keccak(pub_unc[1:])[-20:]) == acct.address

    digest1 = keccak(b"airgap-tx-signer-kat-1")
    digest2 = keccak(bytes.fromhex("deadbeef" * 8))

    def sign_digest(d: bytes) -> dict:
        sig = pk.sign_msg_hash(d)
        v0 = int(sig.v)
        assert v0 in (0, 1)
        v = v0 + 27
        r = int(sig.r)
        s = int(sig.s)
        sig65 = r.to_bytes(32, "big") + s.to_bytes(32, "big") + bytes([v])
        rec = Account._recover_hash(d, vrs=(v, r, s))
        assert rec.lower() == acct.address.lower()
        return {
            "digest": "0x" + d.hex(),
            "r": "0x" + r.to_bytes(32, "big").hex(),
            "s": "0x" + s.to_bytes(32, "big").hex(),
            "v": v,
            "recid": v0,
            "signature_rsv": "0x" + sig65.hex(),
            "recovered_address": rec,
        }

    tx = {
        "nonce": 0,
        "gasPrice": 1_000_000_000,
        "gas": 21000,
        "to": "0x1111111111111111111111111111111111111111",
        "value": 1,
        "data": b"",
        "chainId": 11155111,
    }
    unsigned = serializable_unsigned_transaction_from_dict(tx)
    tx_hash = unsigned.hash()
    signed = Account.sign_transaction(tx, PRIV_HEX)
    recovered = Account.recover_transaction(signed.raw_transaction)

    vectors = {
        "note": "THROW AWAY DEMO KEY ONLY. Never fund this key on mainnet.",
        "private_key": PRIV_HEX,
        "public_key_uncompressed": "0x" + pub_unc.hex(),
        "address": acct.address,
        "keccak_vectors": [
            {
                "name": "kat1",
                "input_hex": "0x" + b"airgap-tx-signer-kat-1".hex(),
                "digest": "0x" + digest1.hex(),
            },
            {
                "name": "deadbeef",
                "input_hex": "0x" + ("deadbeef" * 8),
                "digest": "0x" + digest2.hex(),
            },
            {"name": "empty", "input_hex": "0x", "digest": "0x" + keccak(b"").hex()},
        ],
        "ecdsa_vectors": [
            sign_digest(digest1),
            sign_digest(digest2),
            sign_digest(tx_hash),
        ],
        "legacy_sepolia_tx": {
            "tx": {
                "nonce": 0,
                "gasPrice": 1_000_000_000,
                "gas": 21000,
                "to": "0x1111111111111111111111111111111111111111",
                "value": 1,
                "data": "0x",
                "chainId": 11155111,
            },
            "signing_hash": "0x" + tx_hash.hex(),
            "raw_transaction": "0x" + signed.raw_transaction.hex(),
            "r": "0x" + int(signed.r).to_bytes(32, "big").hex(),
            "s": "0x" + int(signed.s).to_bytes(32, "big").hex(),
            "v": int(signed.v),
            "recovered_address": recovered,
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(vectors, indent=2) + "\n")
    print(f"wrote {OUT}")
    print(f"address {acct.address}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Host-side CLI for airgap-tx-signer.

Phase 1 (no hardware): build unsigned Sepolia legacy tx, print signing hash.
Phase 2 (hardware): talk serial protocol to device for GET_ADDR / SIGN.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def cmd_build_tx(args: argparse.Namespace) -> int:
    from eth_account import Account
    from eth_account._utils.legacy_transactions import serializable_unsigned_transaction_from_dict

    tx = {
        "nonce": args.nonce,
        "gasPrice": args.gas_price,
        "gas": args.gas,
        "to": args.to,
        "value": args.value,
        "data": bytes.fromhex(args.data[2:] if args.data.startswith("0x") else args.data),
        "chainId": args.chain_id,
    }
    unsigned = serializable_unsigned_transaction_from_dict(tx)
    signing_hash = unsigned.hash()
    out = {
        "tx": {
            "nonce": tx["nonce"],
            "gasPrice": tx["gasPrice"],
            "gas": tx["gas"],
            "to": tx["to"],
            "value": tx["value"],
            "data": args.data if args.data.startswith("0x") else "0x" + args.data,
            "chainId": tx["chainId"],
        },
        "signing_hash": "0x" + signing_hash.hex(),
        "note": "Send SIGN <signing_hash> to device after human reviews OLED/LCD summary.",
    }
    print(json.dumps(out, indent=2))
    if args.privkey:
        signed = Account.sign_transaction(tx, args.privkey)
        print(
            json.dumps(
                {
                    "warning": "HOST-SIDE SIGN (debug only). Production path signs on device.",
                    "raw_transaction": "0x" + signed.raw_transaction.hex(),
                    "r": hex(signed.r),
                    "s": hex(signed.s),
                    "v": signed.v,
                },
                indent=2,
            )
        )
    return 0


def cmd_assemble(args: argparse.Namespace) -> int:
    """Attach r,s,v to a legacy tx dict and emit raw tx (host debug helper)."""
    from eth_account import Account
    from eth_account._utils.legacy_transactions import (
        encode_transaction,
        serializable_unsigned_transaction_from_dict,
    )
    from eth_utils import to_int

    tx = json.loads(Path(args.tx_json).read_text() if args.tx_json else args.tx)
    if "tx" in tx:
        tx = tx["tx"]
    r = to_int(hexstr=args.r)
    s = to_int(hexstr=args.s)
    v = int(args.v)
    unsigned = serializable_unsigned_transaction_from_dict(
        {
            "nonce": tx["nonce"],
            "gasPrice": tx["gasPrice"],
            "gas": tx["gas"],
            "to": tx["to"],
            "value": tx["value"],
            "data": tx.get("data") or b"",
            "chainId": tx["chainId"],
        }
    )
    # eth_account encode expects vrs with chain-aware v already
    raw = encode_transaction(unsigned, vrs=(v, r, s))
    print(json.dumps({"raw_transaction": "0x" + raw.hex()}, indent=2))
    try:
        print(json.dumps({"recovered": Account.recover_transaction(raw)}, indent=2))
    except Exception as e:
        print(json.dumps({"recover_error": str(e)}), file=sys.stderr)
        return 1
    return 0


def cmd_serial(args: argparse.Namespace) -> int:
    try:
        import serial  # type: ignore
    except ImportError:
        print("pyserial not installed. activate .venv", file=sys.stderr)
        return 2

    ser = serial.Serial(args.port, args.baud, timeout=args.timeout)
    time.sleep(0.2)
    if args.cmd == "ping":
        ser.write(b"PING\n")
    elif args.cmd == "get-addr":
        ser.write(b"GET_ADDR\n")
    elif args.cmd == "sign":
        digest = args.digest
        if not digest.startswith("0x"):
            digest = "0x" + digest
        ser.write(f"SIGN {digest}\n".encode())
    else:
        print("unknown serial cmd", file=sys.stderr)
        return 2

    deadline = time.time() + args.timeout
    lines = []
    while time.time() < deadline:
        line = ser.readline().decode("utf-8", errors="replace").strip()
        if not line:
            continue
        print(line)
        lines.append(line)
        if line.startswith("ADDR ") or line.startswith("SIG ") or line.startswith("ERR ") or line == "PONG":
            break
        if line == "NEED_CONFIRM":
            print("# device waiting for physical Confirm button", file=sys.stderr)
            deadline = time.time() + max(args.timeout, 60)
    ser.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="airgap-host", description="Host tools for airgap-tx-signer")
    sub = p.add_subparsers(dest="command", required=True)

    b = sub.add_parser("build-tx", help="Build unsigned legacy tx + signing hash")
    b.add_argument("--to", default="0x1111111111111111111111111111111111111111")
    b.add_argument("--value", type=int, default=1)
    b.add_argument("--nonce", type=int, default=0)
    b.add_argument("--gas", type=int, default=21000)
    b.add_argument("--gas-price", type=int, default=1_000_000_000)
    b.add_argument("--chain-id", type=int, default=11155111, help="11155111=Sepolia")
    b.add_argument("--data", default="0x")
    b.add_argument("--privkey", default=None, help="DEBUG only: sign on host")
    b.set_defaults(func=cmd_build_tx)

    a = sub.add_parser("assemble", help="Attach r,s,v to tx JSON and print raw tx")
    a.add_argument("--tx-json", help="Path to JSON with tx fields")
    a.add_argument("--tx", help="Inline JSON string with tx fields")
    a.add_argument("--r", required=True)
    a.add_argument("--s", required=True)
    a.add_argument("--v", required=True)
    a.set_defaults(func=cmd_assemble)

    s = sub.add_parser("serial", help="Talk to device over USB serial (needs hardware)")
    s.add_argument("--port", required=True, help="e.g. /dev/tty.usbmodem...")
    s.add_argument("--baud", type=int, default=115200)
    s.add_argument("--timeout", type=float, default=5.0)
    s.add_argument("cmd", choices=["ping", "get-addr", "sign"])
    s.add_argument("--digest", help="0x-prefixed 32-byte digest for sign")
    s.set_defaults(func=cmd_serial)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

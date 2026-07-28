# airgap-tx-signer

Offline / air-gapped Ethereum transaction signer on a Raspberry Pi Pico (RP2040).

Host builds an unsigned transaction. Device shows details on LCD, waits for physical **Confirm** or **Cancel**, signs with secp256k1 in C, returns `v,r,s`. Host broadcasts.

**Status:** Phase 1 desktop crypto KATs implemented. Firmware pending hardware.

**Safety:** Demo keys only. Testnet only until threat model is real. This is a learning/portfolio signer, not a production HSM.

## Architecture

```text
Internet host                          Air-gapped Pico (C)
----------------                       ----------------------
Build unsigned raw tx
  |                                    |
  +-- USB serial --------------------->|
                                       LCD summary
                                       Confirm / Cancel buttons
                                       Keccak + secp256k1 sign
  |<----- SIG v,r,s -------------------+
Attach signature
eth_sendRawTransaction (testnet)
```

## Repo layout

```text
desktop/     Phase 1 C KATs (keccak + secp256k1 vs eth_account vectors)
host/        Python CLI (build-tx, assemble, serial)
firmware/    Pico firmware stubs (Phase 2)
vectors/     known_answers.json (throwaway demo key)
docs/        threat model + hardware arrival checklist
third_party/secp256k1  bitcoin-core libsecp256k1 (recovery module)
```

## Quick start (no hardware)

```bash
cd ~/Code/airgap-tx-signer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python host/gen_vectors.py
make desktop-test
python host/cli.py build-tx --help
```

Expected: `ALL PASS: 0 failure(s)`

## Hardware kit (arriving)

LAFVIN Pico starter kit BOM is enough:
- Raspberry Pi Pico
- I2C LCD1602
- Breadboard + jumpers + USB cable
- Push buttons (use 2: Confirm + Cancel)

See `docs/hardware-arrival.md`.

## Serial protocol (v1)

```text
-> PING
<- PONG

-> GET_ADDR
<- ADDR 0x...

-> SIGN 0x<64 hex digest chars>
<- NEED_CONFIRM
   (Confirm) <- SIG 0x<r64><s64><v2>
   (Cancel)  <- ERR denied
   (timeout) <- ERR timeout
```

## Phases

1. Desktop C KATs match Python eth_account (done when `make desktop-test` is green)
2. Pico bring-up: USB serial, LCD, 2 buttons
3. Key + address export on device
4. Sign digest with confirm/cancel
5. Host assemble + Sepolia broadcast
6. Harden: on-device tx parse, no blind digest default, optional secure element

## License

MIT. `third_party/secp256k1` retains its own license (MIT).

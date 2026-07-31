# airgap-tx-signer

Offline / air-gapped Ethereum transaction signer on a Raspberry Pi Pico (RP2040).

Host builds an unsigned transaction. Device shows details on LCD, waits for physical **Confirm** or **Cancel**, signs with secp256k1 in C, returns `v,r,s`. Host broadcasts.

**Status:** Phase 1 desktop crypto KATs implemented and green in CI. Phase 2 firmware bring-up code (USB serial `PING`/`PONG`/`VERSION`, LED heartbeat) is written and builds via `make firmware-build`, but is not yet validated against physical hardware — see the unchecked boxes in `docs/hardware-arrival.md`.

**Safety:** Demo keys only. Testnet only until threat model is real. This is a learning/portfolio signer, not a production HSM.

## What this project is

A private key that ever touches an internet-connected machine can be stolen by malware on that machine, no matter how careful the software around it is. Hardware wallets (Ledger, Trezor, etc.) solve this by keeping the key on a separate, purpose-built device that only ever exchanges *unsigned* and *signed* transactions with the host — never the key itself. This project builds that same idea from scratch, in C, on a $4 microcontroller, as a way to actually understand (rather than just trust) how that trust boundary works:

- The **host** (a normal internet-connected computer) knows account balances, builds transactions, and broadcasts signed ones. It never holds the private key.
- The **device** (a Raspberry Pi Pico, deliberately never connected to the internet) holds the private key, shows the human what they're about to sign, and only signs after a physical button press. It talks to the host over a USB serial link that carries plain request/response text — no code execution, no filesystem access, no network stack.
- The two sides are connected only by that serial link, which is why "air-gapped" here means "logically isolated over a narrow, auditable protocol," not "no wire at all."

This is explicitly a **learning/portfolio build**, not a competitor to commercial hardware wallets: the threat model (`docs/threat-model.md`) is upfront about what corners are cut in v1 (e.g. the key can live unencrypted in MCU flash, and the device may sign a bare digest without independently parsing the transaction it represents).

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

Walking through a signing round-trip:

1. **Host builds the transaction** (`host/cli.py build-tx`): nonce, gas price, gas limit, `to`, `value`, `data`, `chainId` go in; it computes the EIP-155 signing hash (`signing_hash`) the same way `eth_account` would, so the device's answer can be checked against a known-good reference during development.
2. **Host sends the digest to the device** over USB serial (`SIGN 0x<digest>`). Today the device signs whatever 32-byte digest it's handed ("blind signing" — see risks below); a later phase has the device parse the raw tx fields itself and render them on the LCD so the human is confirming the *actual* transaction, not just trusting the host's summary.
3. **Device shows a summary and waits.** It responds `NEED_CONFIRM` and blocks until the human presses the physical Confirm or Cancel button (or it times out), so a compromised or buggy host can't get a signature without a person in the loop.
4. **Device signs and returns `r, s, v`** using secp256k1 (via `libsecp256k1`'s recovery module) and Keccak-256, both implemented in portable C so the exact same code paths are exercised on desktop (for testing against known answers) and on-device.
5. **Host reassembles and broadcasts** (`host/cli.py assemble`): attaches `r,s,v` to the unsigned tx, RLP-encodes the raw transaction, and (in later phases) submits it via `eth_sendRawTransaction` on Sepolia testnet.

## Repo layout

```text
desktop/     Phase 1 C KATs (keccak + secp256k1 vs eth_account vectors)
host/        Python CLI (build-tx, assemble, serial)
firmware/    Pico C SDK project: USB serial bring-up now, signing logic in later phases
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

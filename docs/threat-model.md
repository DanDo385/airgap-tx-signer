# Threat model

## What v1 is
A portfolio / learning air-gapped signer:
- Key can live in MCU flash (explicitly INSECURE DEMO STORAGE)
- Host may send a precomputed 32-byte digest (blind signing risk)
- Physical Confirm/Cancel on device
- LCD shows a short human summary when host also sends display fields (Phase 2+)

## What v1 is not
- Not Ledger/Trezor-class
- Not safe for mainnet savings
- Not immune to a malicious host lying about tx contents if device only signs digests
- Not side-channel hardened

## Risks

| Risk | v1 status | Mitigation path |
|---|---|---|
| Key exfil via flash dump / SWD | Vulnerable if key in flash | Secure element later |
| Malicious host lies about tx | Vulnerable if blind digest | On-device parse + LCD fields |
| Accidental sign | Reduced by Confirm/Cancel + timeout | Keep both buttons |
| Network attack on device | Low if USB-only, no Wi-Fi | Never use ESP32 Wi-Fi path |
| Demo key reuse | High if funded | Throwaway keys only |

## Rules
1. Testnet only until Phase 6 hardening.
2. Never put life savings on this device.
3. README and demos must say "learning signer".
4. Zero private key buffers in RAM after sign.

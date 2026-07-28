# Hardware arrival checklist

Target kit: LAFVIN Basic Starter Kit for Raspberry Pi Pico (LCD1602 + buttons + breadboard).

## Unbox verify
- [ ] Pico present (note: headers soldered or not)
- [ ] Micro USB cable works for data (not charge-only)
- [ ] I2C LCD1602 present
- [ ] Breadboard + jumper wires present
- [ ] At least 2 push buttons

If Pico lacks headers: solder pin headers once, or swap to Pico H.

## Software prep (can do before/while unboxing)
```bash
cd ~/Code/airgap-tx-signer
source .venv/bin/activate
make desktop-test
```

Install Pico SDK (macOS):
- Follow https://github.com/raspberrypi/pico-sdk
- Or `brew install picotool` after SDK is present

## Day-1 bring-up order
1. Flash blink / USB serial "hello" (`PONG` to `PING`)
2. Wire LCD1602 on I2C; print `airgap-tx-signer`
3. Wire Confirm + Cancel buttons with debounce
4. Port desktop keccak + secp256k1 into firmware
5. `GET_ADDR` returns address matching host derivation
6. `SIGN` requires Confirm; Cancel returns `ERR denied`
7. Host `cli.py serial` end-to-end on Sepolia

## Wiring sketch (tentative)
- LCD I2C: SDA=GP4, SCL=GP5, VCC=3V3, GND=GND (adjust if backpack differs)
- Confirm button: GP14 to GND (internal pull-up)
- Cancel button: GP15 to GND (internal pull-up)

Document actual pins in firmware README when wired.

## Done definition for first hardware night
- [ ] Serial PING/PONG works
- [ ] LCD shows text
- [ ] Both buttons read reliably
- [ ] Address export works
- [ ] One testnet signature recovered correctly on host (broadcast optional same night)

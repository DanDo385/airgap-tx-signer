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

## Wiring plan (LA045 tutorial reference)
- LCD1602 I2C: SDA=GP0, SCL=GP1, VCC=3V3, GND=GND
- LCD address: start with `0x27`; run an I2C scan before relying on it
- Confirm button: GP14 to GND (internal pull-up, active low)
- Cancel button: GP15 to GND (internal pull-up, active low)

The official [LA045 tutorial archive](https://www.dropbox.com/scl/fo/ynihrh5p4qcsh5mief1en/h?dl=0&rlkey=v442lp2b2dvcct0bhmk0idlgb)
contains a MicroPython LCD helper that uses I2C0 on GP0/GP1 and address `0x27`.
The archive also contains Arduino examples, which are a hardware reference only: this
project uses the Pico C SDK and does not flash the bundled third-party UF2 images.

Document the physically verified pins and address in the firmware README when wired.

## Done definition for first hardware night
- [ ] Serial PING/PONG works
- [ ] LCD shows text
- [ ] Both buttons read reliably
- [ ] Address export works
- [ ] One testnet signature recovered correctly on host (broadcast optional same night)

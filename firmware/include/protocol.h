/*
 * Pico firmware stubs (Phase 2+).
 * Build with Pico SDK after hardware arrives. See docs/hardware-arrival.md.
 *
 * Protocol (USB CDC text lines):
 *   -> PING
 *   <- PONG
 *   -> GET_ADDR
 *   <- ADDR 0x...
 *   -> SIGN 0x<64 hex digest>
 *   <- NEED_CONFIRM
 *   (Confirm button) <- SIG 0x<r 64 hex><s 64 hex><v 2 hex>
 *   (Cancel / timeout) <- ERR denied|timeout|bad_input
 */
#ifndef AIRGAP_PROTOCOL_H
#define AIRGAP_PROTOCOL_H

#define AIRGAP_PROTO_VERSION 1

#endif

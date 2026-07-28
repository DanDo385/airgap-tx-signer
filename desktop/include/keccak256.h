#ifndef AIRGAP_KECCAK256_H
#define AIRGAP_KECCAK256_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Ethereum-style Keccak-256 (not NIST SHA3-256). */
void airgap_keccak256(const uint8_t *data, size_t len, uint8_t out[32]);

#ifdef __cplusplus
}
#endif

#endif /* AIRGAP_KECCAK256_H */

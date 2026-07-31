# airgap-tx-signer
# Desktop Phase 1 KATs + firmware/host scaffolding.

ROOT := $(abspath .)
SECP := $(ROOT)/third_party/secp256k1
SECP_BUILD := $(ROOT)/build/secp256k1
DESKTOP_BUILD := $(ROOT)/build/desktop
PICO_BUILD := $(ROOT)/build/pico
PICO_SDK_PATH ?= $(HOME)/.pico-sdk
PICO_UF2 := $(PICO_BUILD)/airgap_tx_signer_bringup.uf2
PICO_BOOT_VOLUME ?= /Volumes/RPI-RP2

CC ?= clang
CFLAGS ?= -O2 -Wall -Wextra -std=c11
CPPFLAGS += -I$(ROOT)/desktop/include -I$(SECP_BUILD)/include -I$(SECP)/include
LDFLAGS += -L$(SECP_BUILD)/lib
LDLIBS += -lsecp256k1 -lpthread

.PHONY: all deps desktop-test vectors host-check firmware-config firmware-build firmware-flash firmware-help clean

all: desktop-test

deps: $(SECP_BUILD)/lib/libsecp256k1.a

$(SECP_BUILD)/lib/libsecp256k1.a:
	@mkdir -p $(SECP_BUILD)
	cmake -S $(SECP) -B $(SECP_BUILD) \
		-DSECP256K1_ENABLE_MODULE_RECOVERY=ON \
		-DSECP256K1_BUILD_BENCHMARK=OFF \
		-DSECP256K1_BUILD_TESTS=OFF \
		-DSECP256K1_BUILD_EXHAUSTIVE_TESTS=OFF \
		-DSECP256K1_BUILD_CTIME_TESTS=OFF \
		-DSECP256K1_BUILD_EXAMPLES=OFF \
		-DBUILD_SHARED_LIBS=OFF \
		-DCMAKE_BUILD_TYPE=Release \
		-DCMAKE_INSTALL_PREFIX=$(SECP_BUILD)
	cmake --build $(SECP_BUILD) --config Release
	cmake --install $(SECP_BUILD)

vectors: vectors/known_answers.json

vectors/known_answers.json:
	@echo "Run: . .venv/bin/activate && python host/gen_vectors.py"

$(DESKTOP_BUILD)/test_kats: desktop/src/test_kats.c desktop/src/keccak256.c desktop/include/keccak256.h deps
	@mkdir -p $(DESKTOP_BUILD)
	$(CC) $(CFLAGS) $(CPPFLAGS) -o $@ desktop/src/test_kats.c desktop/src/keccak256.c $(LDFLAGS) $(LDLIBS)

desktop-test: $(DESKTOP_BUILD)/test_kats vectors/known_answers.json
	cd $(ROOT) && $(DESKTOP_BUILD)/test_kats vectors/known_answers.json

host-check:
	. $(ROOT)/.venv/bin/activate && python host/cli.py --help

# Phase 2 Pico bring-up. This generates a UF2 only; it cannot write hardware.
firmware-config:
	@test -f "$(PICO_SDK_PATH)/external/pico_sdk_import.cmake" || (echo "Missing Pico SDK at $(PICO_SDK_PATH)"; exit 1)
	cmake -S $(ROOT)/firmware -B $(PICO_BUILD) -DPICO_BOARD=pico -DPICO_SDK_PATH="$(PICO_SDK_PATH)" -DCMAKE_BUILD_TYPE=Debug

firmware-build: firmware-config
	cmake --build $(PICO_BUILD)
	@test -f "$(PICO_UF2)" || (echo "Expected UF2 missing: $(PICO_UF2)"; exit 1)
	@echo "Built $(PICO_UF2)"

# Explicit physical side effect: copy a verified UF2 only to a Pico mounted in BOOTSEL mode.
firmware-flash: firmware-build
	@test -d "$(PICO_BOOT_VOLUME)" || (echo "Pico not mounted at $(PICO_BOOT_VOLUME). Connect while holding BOOTSEL."; exit 1)
	cp "$(PICO_UF2)" "$(PICO_BOOT_VOLUME)/"
	@echo "UF2 copied; Pico should reboot into USB serial firmware."

firmware-help:
	@echo "Build:  make firmware-build"
	@echo "Flash:  hold BOOTSEL while connecting Pico, then make firmware-flash"
	@echo "Serial: use the host CLI after macOS exposes the Pico USB CDC device"

clean:
	rm -rf build

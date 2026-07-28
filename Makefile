# airgap-tx-signer
# Desktop Phase 1 KATs + firmware/host scaffolding.

ROOT := $(abspath .)
SECP := $(ROOT)/third_party/secp256k1
SECP_BUILD := $(ROOT)/build/secp256k1
DESKTOP_BUILD := $(ROOT)/build/desktop

CC ?= clang
CFLAGS ?= -O2 -Wall -Wextra -std=c11
CPPFLAGS += -I$(ROOT)/desktop/include -I$(SECP_BUILD)/include -I$(SECP)/include
LDFLAGS += -L$(SECP_BUILD)/lib
LDLIBS += -lsecp256k1 -lpthread

.PHONY: all deps desktop-test vectors host-check clean firmware-help

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

firmware-help:
	@echo "Firmware builds require Pico SDK after hardware arrives."
	@echo "See docs/hardware-arrival.md"

clean:
	rm -rf build

/*
 * Phase 2 hardware bring-up only.
 *
 * USB CDC protocol implemented here:
 *   PING\n -> PONG\n
 *
 * This target has no signing capability, no key material, and no transaction
 * parsing. It validates the hardware and host serial path before those layers
 * are introduced.
 */
#include <ctype.h>
#include <stdio.h>
#include <string.h>

#include "pico/stdlib.h"
#include "protocol.h"

#define LED_PIN PICO_DEFAULT_LED_PIN
#define LINE_CAPACITY 80U

static void trim_line(char *line) {
    size_t length = strlen(line);
    while (length > 0U && isspace((unsigned char)line[length - 1U])) {
        line[--length] = '\0';
    }
}

static void handle_command(char *line) {
    trim_line(line);

    if (strcmp(line, "PING") == 0) {
        puts("PONG");
        return;
    }

    if (strcmp(line, "VERSION") == 0) {
        printf("AIRGAP_TX_SIGNER %d\n", AIRGAP_PROTO_VERSION);
        return;
    }

    puts("ERR bad_command");
}

int main(void) {
    stdio_init_all();

    gpio_init(LED_PIN);
    gpio_set_dir(LED_PIN, GPIO_OUT);

    char line[LINE_CAPACITY];
    size_t length = 0U;
    absolute_time_t next_blink = make_timeout_time_ms(500);

    for (;;) {
        int character = getchar_timeout_us(0);
        if (character != PICO_ERROR_TIMEOUT) {
            if (character == '\n' || character == '\r') {
                if (length > 0U) {
                    line[length] = '\0';
                    handle_command(line);
                    length = 0U;
                }
            } else if (length < (sizeof(line) - 1U)) {
                line[length++] = (char)character;
            } else {
                length = 0U;
                puts("ERR line_too_long");
            }
        }

        if (absolute_time_diff_us(get_absolute_time(), next_blink) <= 0) {
            gpio_xor_mask(1u << LED_PIN);
            next_blink = make_timeout_time_ms(500);
        }

        tight_loop_contents();
    }
}

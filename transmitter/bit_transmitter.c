// gcc IOT_PROJECT/bit_transmitter.c -o IOT_PROJECT/bit_transmitter -lpigpio -lrt -lpthread
// sudo '/home/pi/IoT/IOT_PROJECT/bit_transmitter'
#include <pigpio.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>  // for exit()

#define BCM_PIN 18  // 使用 BCM GPIO18（pigpio 使用 BCM 編號）
#define SYNC_DURATION 200000 // 單位為 microseconds（200ms）
#define BIT_DURATION 40000 // 單位為 microseconds（40ms）
#define DEBUG_MSG(fmt, args...) do { printf(fmt, ##args); fflush(stdout); } while(0)

// 初始化 transmitter
void transmitter_init() {
    if (gpioInitialise() < 0) {
        fprintf(stderr, "[錯誤] 無法初始化 pigpio\n");
        exit(1);
    }
    gpioSetMode(BCM_PIN, PI_OUTPUT);
}

// 發送同步閃爍 (3 x 200ms)
void transmitter_sync() {
    for (int i = 0; i < 3; ++i) {
        gpioWrite(BCM_PIN, 1);
        gpioSleep(PI_TIME_RELATIVE, 0, SYNC_DURATION);
        gpioWrite(BCM_PIN, 0);
        gpioSleep(PI_TIME_RELATIVE, 0, SYNC_DURATION);
    }
}

// 發送資料 bits
void transmitter_send(const char *bitstring) {
    int len = strlen(bitstring);
    for (int i = 0; i < len; ++i) {
        gpioWrite(BCM_PIN, (bitstring[i] == '1') ? 1 : 0);
        gpioSleep(PI_TIME_RELATIVE, 0, BIT_DURATION);
    }
    gpioWrite(BCM_PIN, 0);
}

// 清理 transmitter
void transmitter_cleanup() {
    gpioTerminate();
}

int main(int argc, char *argv[]) {
    printf("argv: %s\n", argv[1]);
    const char *bitstring = argc>1? argv[1] : "10111001101001101001010101010100111010101001010110001000101001101011100110100110100101010101010011101010111101011010100010100100"; // 你的 bit 串（只放0/1，不要空格）
                                  // received: 10111001101001101001010101010100111010101001010110001000101001101011100110100110100101010101010011101010111101011010100010100100
    printf("size of string: %d\n",sizeof(bitstring)/sizeof(char));
    transmitter_init();
    DEBUG_MSG("[DEBUG] 初始化完成，開始硬體測試...\n");
    transmitter_sync();
    DEBUG_MSG("[DEBUG] 硬體測試完成，開始發送資料...\n");
    transmitter_send(bitstring);
    DEBUG_MSG("[DEBUG] 資料發送完畢\n");
    transmitter_cleanup();

    return 0;
}
//gcc bits_receiver.c -o bits_receiver -lpigpio -lrt -lpthread
//sudo ./bits_receiver
#include <pigpio.h>
#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>  // for exit()

#define GPIO_PIN 18       // wiringPi 1 == BCM 18
#define HIGH 1
#define LOW 0
#define BIT_COUNT 128
#define BIT_DURATION 40000 // 40ms (us)
#define SYNC_DURATION 200000 // 200ms (us)
#define TX_OFFSET 0       // 不再使用固定補償，改用動態對齊

// 初始化 receiver
void receiver_init() {
    if (gpioInitialise() < 0) exit(1);
    gpioSetMode(GPIO_PIN, PI_INPUT);
    gpioSetPullUpDown(GPIO_PIN, PI_PUD_DOWN);
}

// 偵測同步閃爍，回傳第6個邊緣時間
unsigned int detect_sync() {
    int last = gpioRead(GPIO_PIN);
    unsigned int edge_times[6];
    int idx = 0;
    while (idx < 6) {
        int curr = gpioRead(GPIO_PIN);
        if (curr != last) {
            unsigned int now = gpioTick();
            if (idx == 0 || now - edge_times[idx - 1] >= 150000)
                edge_times[idx++] = now;
            last = curr;
        } else {
            gpioDelay(50);
        }
    }
    return edge_times[5];
}

// 動態對齊並回傳資料起始時間
unsigned int dynamic_align(unsigned int sync_time) {
    // 等待首次 falling edge
    while (gpioRead(GPIO_PIN) == HIGH) {
        gpioDelay(50);
    }
    unsigned int fall_time = gpioTick();
    return fall_time + BIT_DURATION / 2;
}

// 接收 bits 到陣列
void receive_bits(int bits[], unsigned int start_time) {
    for (int i = 0; i < BIT_COUNT; ++i) {
        unsigned int sample_time = start_time + i * BIT_DURATION;
        while (gpioTick() < sample_time) {
            gpioDelay(50);
        }
        gpioDelay(BIT_DURATION / 4);
        int raw = gpioRead(GPIO_PIN);
        bits[i] = 1 - raw;
    }
}

// 輸出 bits
void print_bits(int bits[]) {
    for (int i = 0; i < BIT_COUNT; ++i) {
        putchar((char)(bits[i]+48));
    }
    putchar('\n');
    fflush(stdout);
}

// 清理 receiver
void receiver_cleanup() {
    gpioTerminate();
}

int main() {
    receiver_init();
    // printf("等待同步訊號 (3×200 ms 閃爍)…\n");

    // ver1. 偵測同步訊號，並獲取第6個邊緣時間
    // unsigned int sync_edge = detect_sync();
    // unsigned int start_time = dynamic_align(sync_edge);

    // ver2. 使用 detect_sync() 直接獲取同步時間
    unsigned int start_time = detect_sync() + SYNC_DURATION;

    // printf("同步完成，開始接收 %d bits…\n", BIT_COUNT);
    int bits[BIT_COUNT];
    receive_bits(bits, start_time);
    print_bits(bits);
    receiver_cleanup();
    return 0;
}

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
 
// 函数声明
int8_t int_to_8bit_complement(int x);
int8_t add_8bit_complement(int8_t a, int8_t b);
int8_t sub_8bit_complement(int8_t a, int8_t b);
void print_binary(int8_t num);
 
int main() {
    int x, y;
    int8_t x_complement, y_complement;
    int8_t sum, difference;
 
    // 读取两个十进制数
    printf("请输入两个十进制数 x 和 y：\n");
    scanf("%d %d", &x, &y);
 
    // 转换为8位二进制数的补码表示
    x_complement = int_to_8bit_complement(x);
    y_complement = int_to_8bit_complement(y);
 
    // 执行定点补码的加法运算
    sum = add_8bit_complement(x_complement, y_complement);
 
    // 执行定点补码的减法运算
    difference = sub_8bit_complement(x_complement, y_complement);
 
    // 输出结果
    printf("x 的8位二进制补码：");
    print_binary(x_complement);
    printf("\n");
 
    printf("y 的8位二进制补码：");
    print_binary(y_complement);
    printf("\n");
 
    printf("x + y 的8位二进制补码结果：");
    print_binary(sum);
    printf("\n");
 
    printf("x - y 的8位二进制补码结果：");
    print_binary(difference);
    printf("\n");
 
    return 0;
}
 
// 将整数转换为8位二进制数的补码表示
int8_t int_to_8bit_complement(int x) {
    int8_t result;
    if (x >= 128 || x < -128) {
        printf("输入的数字超出8位二进制补码表示的范围（-128到127）\n");
        exit(1);
    }
    if (x < 0) {
        result = (int8_t)(~(x) + 1); // 取反加1得到补码
    } else {
        result = (int8_t)x;
    }
    return result;
}
 
// 8位二进制补码的加法运算
int8_t add_8bit_complement(int8_t a, int8_t b) {
    int16_t temp = (int16_t)a + (int16_t)b; // 临时使用16位整数来防止溢出
    return (int8_t)(temp & 0xFF); // 取低8位，模拟8位运算的结果
}
 
// 8位二进制补码的减法运算
int8_t sub_8bit_complement(int8_t a, int8_t b) {
    int16_t temp = (int16_t)a - (int16_t)b; // 临时使用16位整数来防止溢出
    return (int8_t)(temp & 0xFF); // 取低8位，模拟8位运算的结果
}
 
// 打印8位二进制数
void print_binary(int8_t num) {
    for (int i = 7; i >= 0; i--) {
        printf("%d", (num >> i) & 1);
    }
}
#include <stdio.h>
#include <stdlib.h>
#include <math.h>

// 定义花生植株结构体 
typedef struct {
    int x;          // 植株行号
    int y;          // 植株列号
    int peanuts;    // 该植株的花生数量
} Plant;

// 比较函数，用于qsort排序
int compare(const void *a, const void *b) {
    Plant *plantA = (Plant *)a;  // 转换为Plant指针
    Plant *plantB = (Plant *)b;  // 转换为Plant指针
    return plantB->peanuts - plantA->peanuts; // 按花生数量降序排序
}

int main() {
    // 打开输入文件
    FILE *file = fopen("peanut.txt", "r");
    if (file == NULL) {
        printf("无法打开文件\n");
        return 1;  // 文件打开失败，返回错误码
    }

    int rows, cols, time;  // 花生田行数、列数、时间限制
    // 读取第一行的三个数据，rows存储行，cols存储列，time存储时间 
    fscanf(file, "%d %d %d", &rows, &cols, &time);

    // 分配存储所有植株的内存空间
    Plant *plants = (Plant *)malloc(rows * cols * sizeof(Plant));
    int count = 0;  // 记录实际有花生的植株数量

    // 读取花生田数据
    int i = 0,j = 0;
    for (i = 0; i < rows; i++) {
        for (j = 0; j < cols; j++) {
            int peanuts;
            fscanf(file, "%d", &peanuts);  // 读取每个位置的花生数量
            if (peanuts > 0) {  // 只记录有花生的植株
                plants[count].x = i;       // 记录行号
                plants[count].y = j;       // 记录列号
                plants[count].peanuts = peanuts;  // 记录花生数量
                count++;  // 有效植株计数增加
            }
        }
    }
    fclose(file);  // 关闭文件

    // 按花生数量从多到少排序
    qsort(plants, count, sizeof(Plant), compare);

    int totalPeanuts = 0;    // 总共采摘的花生数量
    int currentTime = 0;     // 当前已用时间
    int currentX = -1;       // 当前位置行号，-1表示在路边
    int currentY = -1;       // 当前位置列号

    // 遍历所有植株，按花生数量从多到少采摘
    for (i = 0; i < count; i++) {
        Plant next = plants[i];  // 获取下一个要采摘的植株
        int timeNeeded;         // 需要的时间
        
        // 计算从当前位置到目标植株需要的时间
        if (currentX == -1) {
            // 如果当前在路边，到第一行植株的时间为行号+1，再加采摘时间1
            timeNeeded = next.x + 1 + 1;
        } else {
            // 如果在田内，计算曼哈顿距离(移动时间)加采摘时间1
            timeNeeded = abs(next.x - currentX) + abs(next.y - currentY) + 1;
        }

        // 计算从目标植株返回路边需要的时间
        int timeToReturn = next.x + 1;
        
        // 检查总时间是否超过限制
        if (currentTime + timeNeeded + timeToReturn <= time) {
            // 时间足够，执行采摘
            if (currentX == -1) {
                currentTime += next.x + 1 + 1;  // 从路边到植株并采摘
            } else {
                currentTime += abs(next.x - currentX) + abs(next.y - currentY) + 1;  // 移动并采摘
            }
            totalPeanuts += next.peanuts;  // 累加花生数量
            currentX = next.x;             // 更新当前位置
            currentY = next.y;
        } else {
            // 时间不够，停止采摘
            break;
        }
    }

    // 输出结果
    printf("最多采到了%d个花生\n", totalPeanuts);
    
    // 释放内存
    free(plants);
    
    return 0;  // 程序正常结束
}
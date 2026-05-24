#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_SIZE 100

// 定义人员结构体
typedef struct {
    char name[50];     // 名字
    char surname[50];  // 姓氏
    char gender;       // 性别：M-男，F-女
} Person;

// 定义循环队列结构体
typedef struct {
    Person data[MAX_SIZE];  // 存储队列元素的数组
    int front;             // 队头指针
    int rear;              // 队尾指针
    int size;              // 队列当前大小
} Queue;

// 初始化队列
void initQueue(Queue *q) {
    q->front = q->rear = 0;
    q->size = 0;
}

// 检查队列是否已满
int isFull(Queue *q) {
    return q->size == MAX_SIZE;
}

// 检查队列是否为空
int isEmpty(Queue *q) {
    return q->size == 0;
}

// 入队操作
void enqueue(Queue *q, Person p) {
    if (isFull(q)) {
        printf("Queue is full\n");
        return;
    }
    q->data[q->rear] = p;
    q->rear = (q->rear + 1) % MAX_SIZE;
    q->size++;
}

// 出队操作
Person dequeue(Queue *q) {
    if (isEmpty(q)) {
        printf("Queue is empty\n");
        exit(1);
    }
    Person p = q->data[q->front];
    q->front = (q->front + 1) % MAX_SIZE;
    q->size--;
    return p;
}

// 打印舞伴配对信息
void printDancers(Person female, Person male) {
    printf("%s %s\t %s %s\n", female.name, female.surname, male.name, male.surname);
}

int main() {
    // 打开输入文件
    FILE *file = fopen("dancer.txt", "r");
    if (file == NULL) {
        printf("无法打开文件\n");
        return 1;
    }

    // 读取总人数
    int total_people, i = 0, round = 1;
    fscanf(file, "%d", &total_people);
    fgetc(file); // 读取换行符

    // 初始化男女队列
    Queue males, females;
    initQueue(&males);
    initQueue(&females);

    // 读取人员数据并分配到相应队列
    for (i = 0; i < total_people; i++) {
        Person p;
        fscanf(file, "%s %s %c", p.name, p.surname, &p.gender);
        if (p.gender == 'M') {
            enqueue(&males, p);
        } else if (p.gender == 'F') {
            enqueue(&females, p);
        }
    }
    fclose(file);

    // 检查是否全是男性或全是女性
    if (females.size == 0 && males.size > 0) {
        printf("参加舞会的都是男性，没有女性可以配对。\n");
        return 0;
    } else if (males.size == 0 && females.size > 0) {
        printf("参加舞会的都是女性，没有男性可以配对。\n");
        return 0;
    } else if (males.size == 0 && females.size == 0) {
        printf("舞会没有任何参加者。\n");
        return 0;
    }

    // 获取用户输入的轮次数
    int n;
    printf("请输入要进行配对的轮次数: ");
    scanf("%d", &n);
    
    // 确定每轮次能配对的数量
    int pairs = (males.size < females.size) ? males.size : females.size;
    
    // 进行n轮配对，但只输出前3轮
    for (round = 1; round <= n; round++) {
        // 只在前3轮输出配对信息
        if (round <= 3) {
            printf("第%d轮舞伴：\n", round);
        }
        
        // 进行配对
        for (i = 0; i < pairs; i++) {
            Person female = dequeue(&females);
            Person male = dequeue(&males);
            
            // 只在前3轮输出
            if (round <= 3) {
                printDancers(female, male);
            }
            
            // 重新入队
            enqueue(&females, female);
            enqueue(&males, male);
        }
        
        // 如果当前轮次超过3轮且没有配对，可以提前结束
        if (pairs == 0 && round > 3) {
            break;
        }
    }

    return 0;
}
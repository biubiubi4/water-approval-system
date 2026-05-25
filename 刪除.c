#include <stdio.h>
#include <string.h>

// 计算满足条件的分数分配方案数
int countSolutions(int N, int T, int P) {
	//N为科目，T为总分，P为每一门课程最低分数 
    // 计算剩余可自由分配的分数（每门课已至少有P分）
    int remaining = T - N * P;
    
    // 如果剩余分数为负，说明无法满足每门课至少P分
    if (remaining < 0) {
        return 0;
    }
    
    // 动态规划数组，dp[i][j]表示i门课程分配j分的方式数
    // 使用long long防止大数溢出
    long long dp[N + 1][remaining + 1];
    memset(dp, 0, sizeof(dp));
    
    dp[0][0] = 1;
    
    // 动态规划填表过程
    int i, j, k; 
    for (i = 1; i <= N; i++) {          // 遍历每门课程
        for (j = 0; j <= remaining; j++) {  // 遍历可能的剩余分数
            // 当前课程可以分配的分数：
            for (k = 0; k <= j ; k++) {
                dp[i][j] += dp[i - 1][j - k];  // 累加方案数
            }
        }
    }
    
    return dp[N][remaining];
}

int main() {
    int N, T, P;
    
    // 输入提示
    printf("请输入课程数量N（非负整数）：");
    scanf("%d", &N);
    printf("请输入总分T（非负整数）：");
    scanf("%d", &T);
    printf("请输入每门课程最低分P（非负整数）：");
    scanf("%d", &P);
    
    // 输入验证：检查是否为负数
    if (N < 0 || T < 0 || P < 0) {
        printf("输入错误：所有输入值都不能为负数！\n");
        return 1;
    }
    
    // 特殊条件处理：当N=T=P=0时定义为0
    if (N == 0 && T == 0 && P == 0) {
        printf("分配方案数为：0\n");
        return 0;
    }
    
    // 计算并输出结果
    int result = countSolutions(N, T, P);
    printf("满足条件的分数分配方案数为：%d\n", result);
    
    return 0;
}
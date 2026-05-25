#include "binarytree.h"

// 定义二叉树节点类型别名
typedef struct node Bnode;

// 递归先序遍历
void PreOrder(Bnode *root) {
    if (root != NULL) {
        printf("%d ", root->data);
        PreOrder(root->lchild);
        PreOrder(root->rchild);
    }
}

// 递归中序遍历
void InOrder(Bnode *root) {
    if (root != NULL) {
        InOrder(root->lchild);
        printf("%d ", root->data);
        InOrder(root->rchild);
    }
}

// 递归后序遍历
void PostOrder(Bnode *root) {
    if (root != NULL) {
        PostOrder(root->lchild);
        PostOrder(root->rchild);
        printf("%d ", root->data);
    }
}

// 非递归先序遍历
void PreOrderNonRecursive(Bnode *root) {
    Bnode *stack[MAXTREEHT];
    int top = -1;
    Bnode *p = root;

    while (p != NULL || top != -1) {
        while (p != NULL) {
            printf("%d ", p->data);
            stack[++top] = p;
            p = p->lchild;
        }
        if (top != -1) {
            p = stack[top--];
            p = p->rchild;
        }
    }
}

// 非递归中序遍历
void InOrderNonRecursive(Bnode *root) {
    Bnode *stack[MAXTREEHT];
    int top = -1;
    Bnode *p = root;

    while (p != NULL || top != -1) {
        while (p != NULL) {
            stack[++top] = p;
            p = p->lchild;
        }
        if (top != -1) {
            p = stack[top--];
            printf("%d ", p->data);
            p = p->rchild;
        }
    }
}

// 非递归后序遍历
void PostOrderNonRecursive(Bnode *root) {
    Bnode *stack[MAXTREEHT];
    int top = -1;
    Bnode *p = root;
    Bnode *lastVisited = NULL;

    while (p != NULL || top != -1) {
        while (p != NULL) {
            stack[++top] = p;
            p = p->lchild;
        }
        while (top != -1 && (stack[top]->rchild == NULL || stack[top]->rchild == lastVisited)) {
            p = stack[top--];
            printf("%d ", p->data);
            lastVisited = p;
        }
        if (top != -1) {
            p = stack[top];
            p = p->rchild;
        }
    }
}

// 主函数
int main() {
    Bnode *root = creat(); // 创建二叉树

    printf("递归先序遍历: ");
    PreOrder(root);
    printf("\n");

    printf("递归中序遍历: ");
    InOrder(root);
    printf("\n");

    printf("递归后序遍历: ");
    PostOrder(root);
    printf("\n");

    printf("非递归先序遍历: ");
    PreOrderNonRecursive(root);
    printf("\n");

    printf("非递归中序遍历: ");
    InOrderNonRecursive(root);
    printf("\n");

    printf("非递归后序遍历: ");
    PostOrderNonRecursive(root);
    printf("\n");

    return 0;
}
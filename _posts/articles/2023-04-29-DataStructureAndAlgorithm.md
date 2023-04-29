---
数据结构与算法（只是记忆点）
---

# 数据结构
*  数组
*  链表
*  栈
*  队列
*  散列表
*  堆
*  二叉搜索树
*  AVL树
*  RB树

# Remarks
## 散列表
### 冲突

*  线性探查

    *  插入，线性循环查找直到 1.找到（覆盖） 2.空位（插入） 3.找到自己（失败）

    *  查找，线性循环查找直到 1.找到（成功） 2.空位（失败） 3.找到自己（失败）

    *  删除，查找要删除的元素然后删除，否则失败。然后移动相同桶子的元素直到 1.空位 2. 找到自己
    
*  拉链法


## 堆
### 插入

1.  插入并保持完全树
2.  通过起泡的方式调整使得堆性成立

### 删除

1.  将最右的叶节点替换根节点
2.  通过沉淀的方式调整使得堆性成立

### 初始化

1. 插入。复杂度`N oog(N)`
2. 专门的初始化步骤

    1.  首先构造完全树
    2.  从下往上逐步调整每个节点
    3.  使得每个节点的子树都是一个堆（对于每一个节点调整而言，调整是自上往下的，和删除算法的第二步类似）
    
    算法复杂度是`O(N)`
      
## 红黑树 vs AVL

### 查询
AVL树比红黑树更平衡，树的深度略浅，搜索速度略快

### 插入
红黑树 最多一次旋转，`log(N)`次颜色改变
AVL 最多一次旋转
红黑树比AVL树略快

### 删除
红黑树 最多一次旋转
AVL 最多`log(N)`次旋转
红黑树比AVL树略快




## 快速排序
参考实现，可能不是最优化，但是不容易出bug
```
#include <utility>
#include <vector>

void quickSort(int a[], int i, int j) {

	// j may be smaller than i
	if (j - i <= 0) return;

	int io = i;
	int jo = j;
	// partition

	// a[i] as pivot
	while(i < j) {

		while(i < j && a[i] <= a[j]) {
			--j;
		}

		std::swap(a[i], a[j]);
		// i == j? OK!
		// a[j] is pivot

		while (i < j && a[i] <= a[j]) {
			++i;
		}
		std::swap(a[i], a[j]);
		// i == j? OK!
		// a[i] is pivot

	}

	// i == io, OK!
	quickSort(a, io, i - 1);
	// i == jo, OK!
	quickSort(a, i + 1, jo);
}

void quickSort(int a[], int n) {

	if (n <= 1) return;
	quickSort(a, 0, n-1);

}


template<class Iter>
void quickSort2(Iter iter, int i, int j) {

	if (j - i <= 0) return;

	int io = i;
	int jo = j;
	// iter[0] as pivot
	while (i < j) {

		while (i < j && iter[i] <= iter[j]) {
			--j;
		}
		
		std::iter_swap(iter + i, iter + j);
		// i == j? OK
		// iter[j] is pivot

		while (i < j && iter[i] <= iter[j]) {
			++i;
		}

		std::iter_swap(iter + i, iter + j);
		// i == j? OK
		// iter[i] is pivot


	}

	// i == io?
	// i == jo?
	quickSort2(iter, io, i-1);
	quickSort2(iter, i+1, jo);

}


template<class Iter>
void quickSort2(Iter iter, Iter end) {
	if (end - iter <= 1) {
		return;
	}
	quickSort2(iter, 0, end - iter - 1);
}
```




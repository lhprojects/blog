---
title: "C++ range based for循环中的生命周期"
date: 2023-04-30
tags: ["C++", "programming", "Range-based for loop"]
categories: ["programming", "C++"]
---

在C++中，Range-based for循环（range-based for loop）是一种简化遍历容器和数组元素的方法。然而，当处理生命周期和临时对象时，可能会遇到一些问题。在本文中，我们将讨论Range-based for循环中的生命周期问题。



# 正确写法
```c++
#include <stdio.h>
#include <initializer_list>
#include <utility>

int main() {
    for(int i : {1, 3, 2}) {
        printf("%d\n", i);
    }
}
```

这段代码会被编译器转换为：

```c++
int main() {
    auto && __range = {1, 3, 2};
    auto __begin = std::begin(__range);
    auto __end = std::end(__range);
    for(__begin != __end; ++__begin) {
        printf("%d\n", * __begin);
    }
}

```

其中 `auto && __range = {1, 3, 2};`的`auto` 被推断为 `std::initializer_list<int>` 。
`{1,2,3}`的生命周期相同被延长到与`__range`相同。


# 错误写法 1
```c++
int main() {
    for(int i : std::move({1, 3, 2}) ) {
        printf("%d\n", i);
    }
}
```

这段代码会被编译器转换为：


```c++
int main() {
    auto && __range = std::move({1, 3, 2});
    ...
}

```
然而，`std::move()` 是一个模板函数。
编译器无法区分这是使用三个数字来初始化一个变量，还是用一个 `initializer_list` 来初始化一个变量。
因此，上面的代码会导致编译错误。


# 错误写法2
```c++
int main() {
    for(int i : std::move(std::initializer_list<int>({1, 3, 2})) ) {
        printf("%d\n", i);
    }
}
```

这段代码会被编译器转换为：


```c++
int main() {
    auto && __range = std::move(std::initializer_list<int>({1, 3, 2})); # 1
    ...
}

```
我们来看 `std::move()` 的实现：

```c++
template<class T>
std::remove_reference_t<T> &&std::move(T &&v) {
    return static_cast<std::remove_reference_t<T>&&>(v);
}
```
返回的是引用。
所以`__range`是对`{1,3,2}`的引用。但是显然作为`std::move()`的参数，它的生命周期在语句#1之后就结束了。
因为由于`__range`引用的对象不存在了，程序的结果是错误的。
参考 https://godbolt.org/z/PMTd4P 。


# 思考

下面的代码为什么是错误的：
```c++

struct Foo {
    std::vector<int> &&items() {
        return m_items;
    }
    std::vector<int> m_items;
};

Foo foo() { return {}; }

for (auto& x : foo().items()) {
}

```

答案：
`foo().items()` 返回一个指向 `m_items` 的引用。
由于 `foo()` 返回一个临时对象，当 `foo().items()` 被调用结束时，
该临时对象已经超出了其生命周期。
因此，返回的引用指向了一个不存在的对象，
导致未定义行为。




# 注：
在C++23中，整个 `range-expression` 的所有临时变量的生命周期都会拓展到整个for循环结束。
这意味着标准委员会已经认识到了这种易犯错误的情况，并对其进行了优化。
在新标准下，程序员将更容易避免这类错误，从而编写更安全、更健壮的代码。







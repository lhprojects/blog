---
title: "`constexpr`"
date: 2017-06-09
tags: ["C++", "constexpr"]
categories: ["Programing", "C++"]
toc: true
---
# C++03中的常量表达式

C++03中就已经有常量表达式了，比如：

```cpp
// len is constant expression
int const len = 3;
int arr[len];
```

C++03中 `const` 关键字扮演着多种角色：

```cpp
// a is varible
int a = 1;

// b is a constant variable
int const b = a;
int arr1[b]; // compile error
             // b is not constant expression

// c is a constant expression
int const c = 1;
int arr2[c]; // ok
```


可见 `const` 关键字可以定义不可更改变量，也可以定义常量表达式。当对不可更改变量的定义满足一定条件时，不可更改变量自动提升为常量表达式。

常量表达式的优势：

- 常量表达式在编译期求值，因此可以用于静态长度数组的长度、模板参数以及 `switch` 的 `case` label。
- 常量表达式是编译期概念，因此可以定义在头文件中。
- 常量表达式没有初始化顺序问题。


## lackage

在 C++03 中，不可变变量默认具有 static 的链接性，例如：

```cpp
// str.h
string const str;

// non-const-str.h
string non_const_str;

// src1.cpp
#include "str.h" // ok
#include "non-const-str.h" // 链接性 error

// src2.cpp
#include "str.h" // ok
#include "non-const-str.h" // 链接性 error
```

虽然让 `len` 具有 static 的链接性解决了 `len` 在不同翻译单元重复定义的问题，是一种简便的解决方案。但是这导致每个翻译单元都一份 `len` 的拷贝，同时也破坏了 `const` 和 `static` 的正交性，实则不是一种优雅的解决方案。


# C++11中的常量表达式

## constexpr variable

C++11中可以使用 `constexpr` 定义 `constexpr variable`，`constexpr variable` 是一种常量表达式，例如：

```cpp
constexpr int a = 1; // a is constant expression
constexpr int b = strlen("abc"); // compile error
                                 // strlen("abc") is not constant expression
```

可见，相比 `const`，`constexpr` 可以保证被定义的对象一定是常量表达式。**如果意图定义常量表达式，那么就使用 `constexpr`。** 这样可以避免编译错误传播。如果意图定义不可更改变量，那么就使用 `const`，可以不管被定义的对象是否被提升为常量表达式。

`const` 只支持定义整数、枚举和指针类型的常量表达式。`constexpr` 除了可以定义 build-in 类型的常量表达式，还可以定义任何 literal-type 类型的常量表达式。


### constexpr variable 储存期和连接性

#### 名字空间作用域的常量表达式

我们知道名字空间作用域的常量表达式都具有 static 链接性，如果不对常量表达式取地址，那么连接性其实没有什么影响。但是一旦对常量表达式取地址，那么这个翻译单元就必须为常量表达式分配内存空间，例如：

```cpp
constexpr int x = 1;

void foo() {
    int arr[x]; // same as int arr[1]
    int const *p = &x; // we have to assign memory place for x now
}
```

这是一个轻微的缺点。


#### 类作用域的常量表达式

我们知道类作用域的常量表达式都是 external 链接性。

```cpp
// Class.h
struct Class {
    static constexpr int N = 1;
};

// Class.cpp
cosntexpr Class::N;
```

`Class::N` 既可以当做编译期常量使用，又有 external 链接性，可以说是名字空间作用域常量表达式的补充。注意这里 initializer 和变量定义是分开的，破坏了在变量定义位置初始化的惯例，但是语言设计只能如此。



## constexpr function

还可以使用`constexpr`定义常量函数，如果不使用常量函数，那么可能代码如下

```cpp
constexpr size_t NElem1 = 4;
char buffer1[4+2*NElem1];
constexpr size_t NElem2 = 4;
char buffer2[4+2*NElem2];
```

我们定义两个buffer(`buffer1` `buffer2`)，每个buffer需要从元素数目(`NElem1` `NElem2`，读者不用管他们到底代表什么含义)计算buffer的大小，那么封装`4+2*NElem`呢？C语言可以使用宏，C++03可以使用模板

```cpp
template<size_t NElem>
struct cal_buffer_size {
    static const size_t value = 4 + 2*NElem;
};

constexpr size_t NElem1 = 4;
char buffer1[cal_buffer_size<NElem1>::value];
constexpr size_t NElem2 = 4;
char buffer2[cal_buffer_size<NElem2>::value];
```


但是使用模板也有缺点那就是，只能适用于常量表达式的情况，对于非常量表达式还要另外写函数。C++11提供了更加强大的常函数。当接受常量表达式时作为参数时，返回值也为常量表达式；当接受变量作为参数时，返回值也为变量；

```cpp
constexpr size_t cal_buffer_size(size_t NElem)
{ 
    return 4 + 2 * NElem; 
}

constexpr size_t NElem1 = 4;
char buffer1[cal_buffer_size(NElem1)];

constexpr size_t NElem2 = 4;
char buffer2[cal_buffer_size(NElem2)];

size_t NElem3 = 1;
char *buffer3 = new char[cal_buffer_size(NElem3)]; // ok

char buffer3[cal_buffer_size(NElem3)]; // compile error
```

### constexpr function的链接性

当我们使用常量函数时候，为了保持常量函数求解常量的能力，用到常量函数的每个编译单元必须包含常量函数实现。常量函数是隐式`inline`的，这样多个编译单元包含同一个常量函数的实现的时候，不会出现连接错误。例如：

```cpp
// size.h
constexpr size_t size(size_t sz) { return sz; }

// src1.cpp
#include "size.h"
int x  = 1;
int xx = size(x); // inline here

// src2.cpp
#include "size.h"
int y  = 1;
int yy = size(y); // inline here
```

注意`inline`函数默认是`external`链接性。所以不同翻译的单元对同一`constexpr` function取地址，结果是相同的。


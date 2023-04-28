
这是2017年的旧文。因为硬盘坏了，原版的markdown丢失了，只剩下了生成软件生成的的html还保留在github上。把这篇旧文稍微整理修改一下，作为记录。


# 整数
C++整数丰富多彩（繁杂无比），整数系统本来是初学阶段首先应该学习的，但是温故而知新（不踩旧坑就不错了），所以来复习一下C++中的整数系统。C++中整数包括（他们最短的名字）分别是

```c++
int, unsigned,
short, unsigned short,
unsigned char, signed char,
char,
char8_t, char16_t, char32_t,
long, unsigned long,
long long, unsigned long
```
C++整数系统的复杂性源于设计之初就语焉不详，为了在不同平台上达到最佳性能，没有规定每一种整数的长度。以现在的眼光看来当然是得不偿失，可移植的代码本来就不好写，可移植的性能更是难上加难。所以后来设计的语言中每种整数类型都是固定长度。当然固定整数长度也有缺陷，比如几乎所有语言中都有一种叫做int的类型，他是典型的整数长度，应该足够长，性能足够好。那么现在就有一个问题，应该将int定位32位还是64位？或许根据平台浮动的定义才是最好的。

# char
C语言之初，char没有确定是有符号的还是无符号的（坑爹）。C++后来补了signed char和unsigned char两种类型，他们的符号性是确定。注意他们的是跟char不同的类型。
（如果曾经在标准中一件事情是没有具体规范的，那么后来标准一般不会补充具体规范，因为大家的代码难免会用到某一平台的具体规范，所以C++委员会再也不会规定char的符号性了）。
后来C++又添加了三种整数类型char8_t, char16_t和char32_t，他们是无符号的整数。（委员会这回总算学聪明了。）

# size_t

C++在std名字空间有无符号整数类型size_t。（为了兼容C，所以在全局名字空间肯定也有size_t）。size_t不是基础整数类型。size_t用于表示储存大小，例如：

```c++
sizeof(some_type) -> size_t
alignof(some_type) -> size_t
offsetof(some_type, member_data) -> size_t
size_t n = 1;
new int[n];
malloc(n);
memcpy(dst, src, n);
```

size_t用于循环和数组下标，例如
```c++
for(size_t i = 0; i < std::size(arr); ++i) {
    arr[i] = 0;
}
```

尽管标准没有明确规定，但是各种标准库容器通常也使用size_t表示各种大小
```c++
std::vector<...>::size_type std::vector<...>::size();
std::vector<...>::size_type == size_t
```
在实际使用中完全可以把他们当作同一类型，这样就简化了程序写法。（不过两种是不同的类型，那么首先通常不会导致任何错误，其次算这个标准库的作者很奇葩）

size_t具体对应那一基本整数类型并不知道，所以你就不知道size_t的长度，最大值，最小值（其实并不！虽然没有规定，但是它一定和指针一样长）,但是生活还要继续，对基本整数的服务必须要有。

```c++
//C版本
<limits.h>
SIZE_MAX //最大整数值
//泛型版本
<climits>
std::limit_traits<size_t>::...
```
# 整数提升

这里我们假设sizeof(char)==1 && sizeof(short)==2 && sizeof(int)>=4 && sizeof(char8_t)==8 && sizeof(char16_t)==16 && sizeof(char32_t)==32。那么提升规则是

- signed char，signed short，unsigned char，unsigned short, char16_t 会被提升为int。
- char 根据char的符号性，提升为int或者unsigned。
- 如果int能够容纳char32_t或wchar_t，那么char32_t或wchar_t提升为int否则提升为unsigned int。
- ...
提升的前提显然是，提升到的类型能够完全容纳原来的类型，所以不用担心提升前后数值的变化。

# 算数运算
翻译摘草标准如下：

- 如果其中一个操作子（操作数）为long double，那么两个操作子都转换为long double。(unsigned) long long转换为long double的时候可能会丢失精度。
- 否则，如果其中一个操作子为double，那么两个操作子都转换为double。unsigned or signed 8 bytes integer转换为double的时候可能会丢失精度。
- 否则，如果其中一个操作子为float，那么两个操作子都转换为float。unsigned or signed 4 or 8 bytes integer转换为float的时候可能会丢失精度。

浮点数这一部分比较简单，关键是对于两个整数的情形：

- 如果两个操作子的符号相同，那么低等级的应当转换为高等级的
- 否则，如果有符号的操作子<=无符号的操作子的等级，那么有符号的整数应当转换为无符号的。
    - int + unsigned -> unsigned + unsigned
    - int + unsigned long -> unsigned long + unsigned long
- 否则，如果有符号的长度比无符号的要长（此时一定满足：有符号的操作子的等级>无符号的操作子），那么无符号的应当转换为有符号的。
    - long long + unsigned -> long long + long long
- 否则，（有符号的操作子的等级>无符号的操作子的其他情形）两者都转换成有符号的操作子的无符号版本。
    - long(assume 32bits) + unsigned -> unsigned long + unsigned long

后三条可以总结为，等级选最高的，除非有符号的整形比无符号的整形长，否则就提升为无符号的版本。


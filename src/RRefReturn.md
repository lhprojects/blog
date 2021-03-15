
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

这段代码被解释为

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


# 错误写法1
```c++
int main() {
    for(int i : std::move({1, 3, 2}) ) {
        printf("%d\n", i);
    }
}
```

这段代码被解释为

```c++
int main() {
    auto && __range = std::move({1, 3, 2});
    ...
}

```
而 `std::move()` 是一个模板。编译器无法区分这是使用三个数字来初始化一个变量，还是用一个`initializer_list`来初始化一个变量。
所以上面的代码编译错误。


# 错误写法2
```c++
int main() {
    for(int i : std::move(std::initializer_list<int>({1, 3, 2})) ) {
        printf("%d\n", i);
    }
}
```

这段代码被解释为

```c++
int main() {
    auto && __range = std::move(std::initializer_list<int>({1, 3, 2})); # 1
    ...
}

```
我们来看`std::move()`
```c++
template<class T>
std::remove_reference_t<T> &&std::move(T &&v) {
    static_cast<std::remove_reference_t<T>&&>(v);
}
```
返回的是引用。
所以`__range`是对`{1,3,2}`的引用。但是显然作为`std::move()`的参数，它的生命周期在语句#1之后就结束了。
因为由于`__range`引用的对象不存在了，程序的结果是错误的。
参考 https://godbolt.org/z/PMTd4P .



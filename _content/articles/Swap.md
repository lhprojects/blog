# Use `std::iter_swap`, `std::ranges::swap` or `using std::swap; swap(...,...)`, don't use `std::swap`.

```c++
#include <vector>
#include <algorithm>
#include <utility>
#include <ranges>

namespace NS {
    struct MyClass {
        //MyClass() = default;
        MyClass(MyClass &&);
        MyClass &operator=(MyClass &&) { }
    };
    void swap(MyClass &, MyClass &);

    struct MyClass2 {
        //MyClass2() = default;
        MyClass2(MyClass2 &&);
        MyClass2 &operator=(MyClass2 &&) { }
    };
}

namespace SwapNamespace {

    template<class T>
    void Swap(T &t1, T &t2) {
        using std::swap;
        swap(t1, t2);
    }
}

void std_swap(NS::MyClass &a, NS::MyClass &b) {
    std::swap(a, b);
}
void std_swap(NS::MyClass2 &a, NS::MyClass2 &b) {
    std::swap(a, b);
}

void unqlified_swap(NS::MyClass &a, NS::MyClass &b) {
    swap(a, b);
}
void unqlified_swap(NS::MyClass2 &a, NS::MyClass2 &b) {
    //swap(a, b); can't compile
}

void std_iter_swap(NS::MyClass &a, NS::MyClass &b) {
    std::iter_swap(&a, &b);
}

void std_iter_swap(NS::MyClass2 &a, NS::MyClass2 &b) {
    std::iter_swap(&a, &b);
}

void SwapNamespace_Swap(NS::MyClass &a, NS::MyClass &b) {
    SwapNamespace::Swap(a, b);
}

void SwapNamespace_Swap(NS::MyClass2 &a, NS::MyClass2 &b) {
    SwapNamespace::Swap(a, b);
}

void ranges_swap(NS::MyClass &a, NS::MyClass &b) {
    std::ranges::swap(a, b);
}

void ranges_swap(NS::MyClass2 &a, NS::MyClass2 &b) {
    std::ranges::swap(a, b);
}
```

```asm
std_swap(NS::MyClass&, NS::MyClass&):
        sub     rsp, 24
        mov     rsi, rdi
        lea     rdi, [rsp+15]
        call    NS::MyClass::MyClass(NS::MyClass&&) [complete object constructor]
std_swap(NS::MyClass2&, NS::MyClass2&):
        sub     rsp, 24
        mov     rsi, rdi
        lea     rdi, [rsp+15]
        call    NS::MyClass2::MyClass2(NS::MyClass2&&) [complete object constructor]
unqlified_swap(NS::MyClass&, NS::MyClass&):
        jmp     NS::swap(NS::MyClass&, NS::MyClass&)
unqlified_swap(NS::MyClass2&, NS::MyClass2&):
        ret
std_iter_swap(NS::MyClass&, NS::MyClass&):
        jmp     NS::swap(NS::MyClass&, NS::MyClass&)
std_iter_swap(NS::MyClass2&, NS::MyClass2&):
        sub     rsp, 24
        mov     rsi, rdi
        lea     rdi, [rsp+15]
        call    NS::MyClass2::MyClass2(NS::MyClass2&&) [complete object constructor]
SwapNamespace_Swap(NS::MyClass&, NS::MyClass&):
        jmp     NS::swap(NS::MyClass&, NS::MyClass&)
SwapNamespace_Swap(NS::MyClass2&, NS::MyClass2&):
        sub     rsp, 24
        mov     rsi, rdi
        lea     rdi, [rsp+15]
        call    NS::MyClass2::MyClass2(NS::MyClass2&&) [complete object constructor]
ranges_swap(NS::MyClass&, NS::MyClass&):
        jmp     NS::swap(NS::MyClass&, NS::MyClass&)
ranges_swap(NS::MyClass2&, NS::MyClass2&):
        sub     rsp, 24
        mov     rsi, rdi
        lea     rdi, [rsp+15]
        call    NS::MyClass2::MyClass2(NS::MyClass2&&) [complete object constructor]
```

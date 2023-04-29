---
title: C++ 整型备忘
tag: c++
---


# `std::chrono`
https://godbolt.org/z/G4qaTM
```c++
#include <chrono>
using sec = std::chrono::milliseconds;
using frame =  std::chrono::duration<int32_t, std::ratio<1,60> >;
auto foo(sec i, frame j) {
    return i + j;
}
```

clang -O2
```asm
foo(std::__1::chrono::duration<long long, std::__1::ratio<1l, 1000l> >, std::__1::chrono::duration<int, std::__1::ratio<1l, 60l> >): # @foo(std::__1::chrono::duration<long long, std::__1::ratio<1l, 1000l> >, std::__1::chrono::duration<int, std::__1::ratio<1l, 60l> >)
        lea     rcx, [rdi + 2*rdi]
        movsxd  rax, esi
        imul    rax, rax, 50
        add     rax, rcx
        ret
```
gcc -O2
```asm
foo(std::chrono::duration<long, std::ratio<1l, 1000l> >, std::chrono::duration<int, std::ratio<1l, 60l> >):
        movsx   rsi, esi
        lea     rdx, [rdi+rdi*2]
        lea     rax, [rsi+rsi*4]
        lea     rax, [rax+rax*4]
        lea     rax, [rdx+rax*2]
        ret
```

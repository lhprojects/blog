
# `std::chrono`
```c++
#include <chrono>
using sec = std::chrono::milliseconds;
using frame =  std::chrono::duration<int32_t, std::ratio<1,60> >;
auto foo(sec i, frame j) {
    return i + j;
}
```

```asm
foo(std::__1::chrono::duration<long long, std::__1::ratio<1l, 1000l> >, std::__1::chrono::duration<int, std::__1::ratio<1l, 60l> >): # @foo(std::__1::chrono::duration<long long, std::__1::ratio<1l, 1000l> >, std::__1::chrono::duration<int, std::__1::ratio<1l, 60l> >)
        lea     rcx, [rdi + 2*rdi]
        movsxd  rax, esi
        imul    rax, rax, 50
        add     rax, rcx
        ret
```

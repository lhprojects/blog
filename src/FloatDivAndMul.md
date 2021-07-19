## Division is slow, do it once or in compiling time
```
b = ...
for loop:
  a = ...
  a/b 
  a/1.1
```
After optimization
```
b = ...
c = 1/b
for loop:
  a = ...
  a*c
  a*(1./1.1)
```

# But they are not the same
```c++
double c = 1.01;
double d = 0.99;
double one = 1.;
int main()
{
    printf("%.19E %.19E", c / d, c * (one / d));
    // 1.0202020202020201101E+00 1.0202020202020203321E+00
}
```

# effection
```c++
#include <chrono>
using fseconds = std::chrono::duration<double>;
using fmicroseconds = std::chrono::duration<double, std::micro>;
double foo(double us) {
    fseconds a = fmicroseconds{us};
    return a.count();
}
```
The generated instructions:
```
.LCPI0_0:
        .quad   0x412e848000000000              # double 1.0E+6
foo(double):                                # @foo(double)
        divsd   xmm0, qword ptr [rip + .LCPI0_0]
        ret
```


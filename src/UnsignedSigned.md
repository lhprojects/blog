

# 溢出
根据c++标准，无符号整数代数运算溢出，结果会回卷（wrap）。但是无符号整数代数运算溢出，后果是未定义的（UB）。
编译器，尤其是gcc特别喜欢假定有符号整数的运算永远不会溢出。这么做是符合标准的，因为既然标准规定溢出的后果是未定的，那么假定不会溢出生成的代码产生的结果也是符合标准的。

# 确定性
我们来考虑整数的加法。我们知道有符号的整数是采用补码的形式（尽管c++标准没有规定，但是这就是实际情况）。这导致，有符号的整数的加法和无符号的整数的加法在二进制角度看来是同一操作，只是后续对数值大小的解释不同。实际上在x86-64平台上，对有符号整数和无符号整数加法是相同的指令，而且当加法溢出的时候就会回卷。 例如：
```c++
unsigned unsigned_add(unsigned a, unsigned b) {
    return a + b;
}

int signed_add(int a, int b) {
    return a + b;
}
```
生成了相同的指令：
```asm
unsigned_add(unsigned int, unsigned int): # @unsigned_add(unsigned int, unsigned int)
  lea eax, [rdi + rsi]
  ret
signed_add(int, int): # @signed_add(int, int)
  lea eax, [rdi + rsi]
  ret
```
考虑
```c++
bool overflow(int a) {
    return signed_add(a, 1) < a;
}
```
如果signed_add没有被内联，那么将会检测`a+1`是否会溢出。如果signed_add被内联，那么上面的代码将会被优化为
```c++
bool overflow(int a) {
    //return a + 1 < a;
    return false;
}
```
因为我们假定了`a+1`永远不会溢出，此时`a+1<a`永远为假。
```asm
overflow(int): # @overflow(int)
  xor eax, eax
  ret
```
在当前标准，整数溢出的后果是未定义的。所以结果的不确定性，实际上并不违反标准。但是如果程序在一种编译选项下运行很好，但是在另外一种编译选项下运行不好，那么这是很恼人的。我们需要确定性的结果，如果有bug那么一定要确定性的呈现出来。

# 性能
但是假定有符号整数不会溢出确实带来了给程序整体带了10%的性能改进。举一个比较真实的例子
```c++
int signed_copy(int *v, int i) {
    return v[i]+ v[i+1];
}

int unsigned_copy(int *v, unsigned i) {
    return v[i]+ v[i+1];
}
```
来看看相应的gcc反汇编代码
```asm
signed_copy(int*, int): # @signed_copy(int*, int)
  movsxd rcx, esi
  mov eax, dword ptr [rdi + 4*rcx + 4]
  add eax, dword ptr [rdi + 4*rcx]
  ret
unsigned_copy(int*, unsigned int): # @unsigned_copy(int*, unsigned int)
  mov ecx, esi
  add esi, 1
  mov eax, dword ptr [rdi + 4*rsi]
  add eax, dword ptr [rdi + 4*rcx]
  ret
```

unsigned_copy生成的代码之所以糟糕，是因为你不能假定无符号整形不会溢出。我们必须花时间考虑是否有溢出发生，最廉价的考虑方法就是，去做代数运算，然后使用代数运算的结果。所以使用有符号的整数能够带来性能改进是真实的。

不过对于
```c++
for(unsigned i = ..; i < ..; i++) {
    ...
}
```
这样代码，编译器一般会做循环展开，所以有符号整数带来的劣势不太明显。

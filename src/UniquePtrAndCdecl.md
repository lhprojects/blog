# unique_ptr 与 Itanium C++ ABI

这不是一篇介绍如何使用c++中std::unique_ptr的文章。假定读者已经对unique_ptr的使用和**实现**非常熟悉了。

最近看了这个[视频](https://www.youtube.com/watch?v=rHIkrotSwcc) ，然后自己再收集了一些资料，有些感悟记录如下。

## unique_ptr不是零开销

std::unique_ptr一般被认为是zero-overhead或者说和raw pointer（裸指针）一样高效的。但是实际上不是这样的。
下面我们举例来说明。

我们以raw pointer为基准，一个简单的c++程序为：
```c++
void bar(int*p) noexcept;

__attribute__((noinline)) void baz_rawpointer(int *p)  noexcept {
    global_v = *p;
    delete p;
}
void use_rawpinter(int *p)
{
    bar(p);
    baz_rawpointer(p);
}
```
然后我们使用std::unique_ptr实现相同的功能：
```c++
__attribute__((noinline)) void baz_unique_ptr(std::unique_ptr<int> p) noexcept { 
    global_v = *p;
}

void use_unique_ptr(std::unique_ptr<int> p)
{
    bar(p.get());
    baz_unique_ptr(std::move(p));
}
```

我们比较他们的反编译代码：
        
```asm
baz_rawpointer(int*): 
  movl (%rdi), %eax          # load the integer from pointer
  movl %eax, global_v(%rip)  # save the integer to global
  jmp operator delete(void*)
use_rawpinter(int*):
  pushq %rbx
  movq %rdi, %rbx
  callq bar(int*)
  movq %rbx, %rdi
  popq %rbx
  jmp baz_rawpointer(int*)
```

```asm
baz_unique_ptr(std::unique_ptr<int, std::default_delete<int> >):
  movq (%rdi), %rax          # load pointer from pointer
  movl (%rax), %eax          # load integer from pointer
  movl %eax, global_v(%rip)  # save integer to global
  retq
use_unique_ptr(std::unique_ptr<int, std::default_delete<int> >): 
  pushq %r14
  pushq %rbx
  pushq %rax
  movq %rdi, %rbx
  movq (%rdi), %rdi
  callq bar(int*)
  movq (%rbx), %r14
  movq %r14, (%rsp)
  movq $0, (%rbx)
  movq %rsp, %rdi
  callq baz_unique_ptr(std::unique_ptr<int, std::default_delete<int> >)
  testq %r14, %r14           # here is test instruction
  je .LBB3_1
  movq %r14, %rdi
  addq $8, %rsp
  popq %rbx
  popq %r14
  jmp operator delete(void*)
```

可以看到std::unique_ptr代码更长一些，所以通常也更慢一些。
我们总结std::unique_ptr对程序的两个负面影响

- unique_ptr必须通过压栈，再传递地址的方式来传递参数。被调用的函数要访问unique_ptr中的原始指针，多了一个间接层。

- 调用者清理临时unique_ptr，但是调用者不知道被调用者如何蹂躏了这个临时变量，所以调用者无法做出足够的优化。


## Itanium C++ ABI 调用约定

为了说明std::unique_ptr为什么生成的指令更多，我们下考虑一个更简单的例子。考虑如下的代码：
```c++
void foo(unique_ptr<int> t);
void bar() {
    unique_ptr<int> p(new int);
    foo(std::move(p));
}
```
现在考虑一个问题，调用foo的时候，参数是如何传递进去的？
GCC/Clang通常使用Itanium C++ ABI约定。
在Itanium C++ ABI调用约定里，对于non-trivial的pass-by-value参数，我们首先会在**栈**中创建一个临时变量，
然后把临时变量的地址传递给被调用的函数，
函数调用完毕后，**调用者再清理临时变量**（比如调用析构函数）。
std::unique_ptr就是non-trivial的，因为它具有一个non-trivial的析构函数。

所以上边的代码就类似于
```c++
void foo(unique_ptr<int> *pt);
void bar() {
    unique_ptr<int> p(new int);
    unique_ptr<int> t = std::move(p);
    foo(&t);
    t.~unique_ptr<int>(); // if(t.get()) delete t.get()
    // p.~unique_ptr<int>(); 可以被优化掉
}
```
注意在foo函数中不会调用t的析构函数。
这种调用者负责清理临时变量的做法，使得这种调用约定不能实现真的的move语义。
如果可以实现真正的move语义的话，那么指针的所有权已经转移给foo了，我们应当在foo函数里调用析构函数。
真转移所有权具有稍微更高的效率。
上面的代码中，注意，我们把`t`的地址传递给了`foo`。
如果`foo`把`t`移动到了别的地方，那么`bar`运行` t.~unique_ptr<int>()`时候，就不应该去释放内存。
如果`foo`没有动`t`，那么`bar`运行`t.~unique_ptr<int>()`时候，就应该释放资源。但是调用者根本不知道`foo`是否真的消化了这个unique_ptr，只能老老实实的生成如下的代码
```c++
if(t.get()) delete t.get();
```
对于真转移所有权的做法，foo函数知道自己拥有所有权或者所有权又被转移了，因而不需要判断t.get()是否为空，直接delete t.get()就好了。


## Clang的[[clang::trivial_abi]]

clang允许对类添加 [[clang::trivial_abi]] 属性，这是非标准c++的拓展 [1] [2]，具有如下效果

- 第一，类本身（它本身的全部就是一个原始指针）通过寄存器传递。

- 第二，被调用者清理临时变量。

为了验证[[clang::trivial_abi]]的效果，我们测试c++代码如下：

```c++

#ifdef __clang__ 
#define TRIVAIL_ABI [[clang::trivial_abi]]
#else
#define TRIVAIL_ABI
#endif

template<class T>
struct TRIVAIL_ABI trivial_unique_ptr {
    trivial_unique_ptr() = default;
    explicit trivial_unique_ptr(T *p) : p_(p) {}    
    trivial_unique_ptr(trivial_unique_ptr && r) : p_(std::exchange(r.p_, nullptr)) { }    

    trivial_unique_ptr &operator=(trivial_unique_ptr && r)  {
        std::swap(p_, r.p_);
    }    

    trivial_unique_ptr(trivial_unique_ptr const &r) = delete;  
    trivial_unique_ptr &operator=(trivial_unique_ptr const &r)  = delete;

    T * get() { return p_; }
    ~trivial_unique_ptr() { if(p_) delete p_; }
private:
    T *p_ = nullptr;
};


__attribute__((noinline)) void baz_trivial_unique_ptrt(trivial_unique_ptr<int>) noexcept {
    global_v = *p;
}


void use_trivial_unique_ptrt(trivial_unique_ptr<int> t)
{
    bar(t.get());
    baz_trivial_unique_ptrt(std::move(t));
}
```

其生成的反汇编代码与raw pointer结果一样。

但是这种改变abi的方法也是有缺点的。 
1. 只适用于clang编译器
2. 不是标准Itanium C++ ABI，不能适用于std::unique_ptr。因为Itanium C++ ABI的std::unique_ptr已经广泛被使用了。
3. 如果只是对unique_ptr开后门的话，那么在所有参数的临时变量中，unique_ptr是最先析构的。那么就不能保证参数的构造顺序和析构顺序就完全的相反。（见视频[问答环节](https://www.youtube.com/watch?v=rHIkrotSwcc) )。因而这种ad-hoc的处理方法，可能永远无法成为c++标准的一部分。

## ticket类

std::unique_ptr作为参数传递效率不高，而raw pointer又太危险，有没有折中的方法呢？
在Itanium C++ ABI里，std::unique_ptr不能通过寄存器传递的主要阻碍是Std::unique_ptr有非trivial的析构函数。
我们可以实现一个只包含trivial析构函数的智能指针。
注意下面的代码和原始代码[3]有些许不同。
```c++


template<class T>
struct ticket {
    ticket() = default;
    explicit ticket(T *p) : p_(p) {}
    ticket(std::unique_ptr<int>&& p) : p_(p.release()) {}
    std::unique_ptr<T> redeem() { return std::unique_ptr<T>(std::exchange(p_, nullptr)); }
private:
    T *p_ = nullptr;
};

__attribute__((noinline)) void baz_ticket(ticket<int> t) noexcept {
    auto p  = t.redeem();
    global_v = *p;
}

void use_ticket(ticket<int> t)
{
    auto p = t.redeem();
    bar(p.get());
    baz_ticket(std::move(p));
}

```

使用ticket类有几点好处：
1. 性能和使用raw point完全一样。指针本身通过寄存器传递，被所有权拥有者负责析构。
2. 易用性，表义性比raw pointer好，你知道它试图起到类似unique_ptr的作用。
3. 不需要改变ABI。

但是ticket类依然有几个缺点：

1. 本质上还是raw pointer，没有任何资源管理能力. 在参数传递过程中如果发生异常，会出现资源泄露。
2. 本质上还是raw pointer，没有任何资源管理能力. 在参数传递过程中如果发生异常，会出现资源泄露。
3. 本质上还是raw pointer，没有任何资源管理能力. 在参数传递过程中如果发生异常，会出现资源泄露。



## 参考阅读：

完整代码见[链接](https://godbolt.org/#z:OYLghAFBqd5QCxAYwPYBMCmBRdBLAF1QCcAaPECAM1QDsCBlZAQwBtMQBGAFlICsupVs1qhkAUgBMAISnTSAZ0ztkBPHUqZa6AMKpWAVwC2tEJIAMpLegAyeWpgByxgEaZiXAOykADqgWE6rR6hiZmln4BanR2Ds5Gbh6c3koq0bQMBMzEBCHGphaKypiqQZnZBLFOru5eilk5eWGFCg2V9tUJtckAlIqoBsTIHADkUgDM9siGWADU4uM6RphGJACeC9ji5gCCE1MzmPOLbMAkhAhGm9t7uwQrPsL3CzrTzAoKswAq17utxAZVLM1MgANaYAjzTyyXazOHAvBgiEQHrHAAisywVGYBlYBAWMJ28NmmAAHo9EYQEUiCBAvrMAFQ%2BVEgWY%2BAD6EGZUNknjRN2JIPBtNa6BAIAMtDwAEcDJh2T4CMQXvZ8eMtpIAGxSTVsllszk%2BAB0xGK70wKNR4mh1v5sPhovFkplcoVSpeP3Vs1NWBWKJ53ohg1os0dEqlsvliuVi092AgYbJyAQImAFo5pFmtFxrGjPR6BKhdp2PmIeAAbsx7iABfD6Uz2eisznowSbra27t25JJlQsbN2ey3qJB/Muz2sR1vgAlACSADUdrObOydtJZ/MAKyybfD0AgJUVvBsdnMFx4cSb/lX7vjZRKW%2BThwzhdLldr2e36x4Kjtu4PJ5MBeN4Pm%2BX4dn%2BQFIS%2BOdF2XVd12BMty2PVh2WdSM3WIHlazhQ8UJPDDXWjf0FgxLEcTxTsiXhMkKWQKl8NQ9CI2IpU6UZblWQ5LkrRtPliVwpCj0I1io3YpjRJdcTsJ1HVvX1HjE1JZNUwtYgjQzZtWFzJV8wDW1BK7e08OQ5iiJk%2BYtVQHx3CrEgyIgSS0IsrCrO1LUFLha1CWJYkwwUAB3ZgfC5dlMw0jkC3GXz4UMuLjJo0yRJcsSsKcsypMw6NZjQWhWnc4grXGcjimeGLvJM4SCNS6S3J1Gy7KIGM0QylKWLqnK8oKnUiu8krMTKoCYr/JLvkZWY01pPjpEDAhgwNQsOyqgA/ZyOuy9iZtmH8wtRLB2HuRaKuWktkKrDghPrDkm2zHTWxGrs%2BWo0abnLVA8HQWYXGyCBVSZVFaFQJNMEVF7dkHKtDxcAx7kHKAgfsVgOn097Pu%2B5gAC92WIZhAr8VV3D%2B%2BhONRLNgZU0HIR8oSDohI4fBe57djRr6DCUHG8Z8QniGJyEAfbG0qp%2B3nmWo4kfux3H8Y%2B%2BgibFx69mZ24Vchghodh%2BVOQgRHaGRhxUY%2Br7JY2tjebDVyHp0VVNkBinhkVAMEqV4s3qN2Z2flS32IttKrZtr0xae2K4RFrkjSmy1xfhE3vfNggxRAVZy3TfMmddxK1Y1uHtd1/XMEN9GTfWuPaRLv33UWAPsDtkHHZpp6M5V1mPY58vOqVMvMtqzaY2t%2BhNmBAtg6EsOCAj5E08ViWsfZdve5FBPxWTi0CCnwlTtGrOyxhnOEdl/PC%2BN2ehWRU%2B1X7tVsCH8m6%2BpoWxpxIg2X6jFx59TA/Wijflbd9HPbnoiYUTkgEQhVAPL0a9BYh1mE/VAL8yLAhNJgX0RgUTR1Dr9Y0kd16jxPqAxeicV68W/oLJuIw%2BisBACMTcIxSCmBGOYOhqBqE6DkHIUMAwhhHAmJwOhBBqFMPzKQUEIBxibiNOMSQ3BJDJG4OYTUWpzCeE3EIah3A6EMKYaQFhIw6EKBAJYARjCKGkDgLAJAaAjDc3YGQCgEArE2NqMATg5hJCkCoHgPE7gDEQBcIIuh55aDZDWNQvhpArHLHoAAeT1qEkxpAsBGFTOwAJiS8CmlKCnAxCSyQlE1mEuhhMqEjHCcjFwuNiBrD0FgQppBDxGACX0Gg9AmBsA4DwfgghhCiBQOwmQQg8AuAMZAPoNl0g5IALTRPGLMSZooyISBkHIZI%2BjiilA0BAawTRTDiKsNoKo8REhcFUZEQIdAdliNOf4c5tBDk1CSKo1IJR0jlEaPofIVyihpDKG0e5XRHn1AqJcvZrQKj/OOZwTcfQFBcOGFwSh1DaH0LSbo0kAAOTUkzNTcEmsgZAsxXFGkkLMCAuBCAkCsuMTgmY9DWK8e4KlnBURsOWTIfhTS%2BiiKkUaTUm50U9nRZ4cY8iACc5hOBajUSMDRpBGmuMsFo5h1D9GGPqU0sxMBEAoFQPS2x5BKCOIZR4PcnBXE0s8d44gvj/EJKCSEupkStAEFiaweJ2ikkpNGB6jJLyKyYBydovJyACmlKKXLEpZShmVOqRgUY4SGkapaYwFgqTOkCHcT0sQ/T5DlJGSiHRioghTJmXMhZJUlmyBkKs75frNnbI%2BWEGl1gIXdF8Dc9IlyaVnPSK2pItaNkZDaF2gdry/kdCOW2sF7zQimBpdO9ocQHkIv6IMeFzLpXIqVTo6hGKsU4tylmwlnAjTmCNJwUl5LmpMtpbqpxskeySBZTmjlJjhHcskKe5Im5uDjHRZuUVOLRWSulbK7dujVVGM5dKyQmjUUqvVW%2BvoKdrVBBANwIAA%3D%3D%3D)

[1] https://reviews.llvm.org/D63748

[2] https://quuxplusone.github.io/blog/2018/05/02/trivial-abi-101/

[3] https://quuxplusone.github.io/blog/2019/09/21/ticket-for-unique-ptr/


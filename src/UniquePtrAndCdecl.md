# unique_ptr 与 Itanium C++ ABI

这不是一篇介绍如何使用c++中std::unique_ptr的文章。假定读者已经对unique_ptr的使用和**实现**非常熟悉了。

最近看了这个[视频](https://www.youtube.com/watch?v=rHIkrotSwcc) ，然后自己再收集了一些资料，有些感悟记录如下。

## Itanium C++ ABI 调用约定

考虑如下的代码
```c++
void foo(unique_ptr<int> t);
void bar() {
    unique_ptr<int> p(new int);
    foo(std::move(p));
}
```
考虑一个问题，调用foo的时候，参数是如何传递进去的？
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

具体的反汇编代码可以证明这种推断。
我们以raw pointer为最优化的基准，c++代码为
```c++
void bar(int*p) noexcept;

__attribute__((noinline)) void baz_rawpointer(int *p)  noexcept {
    delete p;
}
void use_rawpinter(int *p)
{
    bar(p);
    baz_rawpointer(p);
}
```
std::unique_ptr的c++代码为
```c++
__attribute__((noinline)) void baz_unique_ptr(std::unique_ptr<int>) noexcept {    
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
  testq %rdi, %rdi
  je .L1
  movl $4, %esi
  jmp operator delete(void*, unsigned long)
.L1:
  ret
use_rawpinter(int*):
  pushq %rbp
  movq %rdi, %rbp
  call bar(int*)
  movq %rbp, %rdi
  popq %rbp
  jmp baz_rawpointer(int*)
```

```asm
baz_unique_ptr(std::unique_ptr<int, std::default_delete<int> >):
  ret
use_unique_ptr(std::unique_ptr<int, std::default_delete<int> >):
  pushq %rbx
  movq %rdi, %rbx
  movq (%rdi), %rdi
  call bar(int*)
  movq (%rbx), %rdi
  movq $0, (%rbx)
  testq %rdi, %rdi
  je .L7
  movl $4, %esi
  popq %rbx
  jmp operator delete(void*, unsigned long)
.L7:
  popq %rbx
  ret

```

现在我们总结std::unique_ptr对程序的两个负面影响

- unique_ptr必须通过压栈，再传递地址的方式来传递参数。被调用的函数要访问unique_ptr中的原始指针，多了一个间接层。

- 调用者清理临时unique_ptr，但是调用者不知道被调用者如何蹂躏了这个临时变量，所以调用者无法做出足够的优化。

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



## 附录
完整代码见[链接](https://godbolt.org/#z:OYLghAFBqd5QCxAYwPYBMCmBRdBLAF1QCcAaPECAM1QDsCBlZAQwBtMQBGAFlICsupVs1qhkAUgBMAISnTSAZ0ztkBPHUqZa6AMKpWAVwC2tQVvQAZPLUwA5YwCNMxLgGZSAB1QLC62nsMTQS8fNTorG3sjJxdeJRUw2gYCZmICAONTTkVlTFU/ZNSCCLtHZzdFFLSMoOyFKuLrUujy7gBKRVQDYmQOAHIpV2tkQywAanFXHSNMIxIAT0nscQAGAEFB4dHMCam2YBJCBCMl1Y31glmPYUvJnRHmBQUxgBVT9friA1UxtWQAa0wBAmAHZZOsxpDfngAUCIG1dgARMZYKjMAysAiTcFrKFjTAAD2uMMI0NhBAgLzGACoPAiQGMPAB9CB00GyEGIs54v6Ain1dAgEAGWh4ACOBkwTI8BGId2sWNcy0kADYpCrGfTGSyPAA6Yi5R6YeEI8Rgs1ciFQgVCkXiyXS2V3N5KsYGrCzeHst1A7q0MY24WiiVSmVyqYu7AQQOE5AIETAY3M0hjWgY1hhtptbGgy1rDzEPAAN2YlxA3KhVNpTKRqfTYexZwtjfWTckQyoqLGTKZD1EPYmrfbqKarwASgBJABqawnFiZa2kE4mAFZZGu%2B6AQLLi3g2EzmA48OIV1zT23XMolBeRzZx9PZ/PFxOL%2BY8FQmxcrjdMHcHk9XneNZPm%2BYEXknGc5wXJdfkLIs91YJk7RDR1iHZCtIR3eD92Qh0wy9SZkVRdFMRbXEoUJYlkFJLCEKQ4M8NlSkaTZBlmVZU1zU5PEMNg3ccIY0MmNogT7SEtD1XVN0tXYmMCTjBNjWIXVkzrVgM1lLNvQtHjWytTC4Lo3DxImVVUA8ZxSxIQiIBExDjNQ0y1VVaTITNHE8TxQMFAAd2YDxWSZFNlOZbNXA8qEdMivTyIM/j7ME1DbMM0SULDMY0FoeonOIU1XCI3JbnCtz9L47CErExz1XMyyiHDRFkvi%2BjKvSzLsvVXK3PylFCt/cLP1i14aTGRMKU46QfQIP1tRzZtSoAPzs5q0qY8axnfQKESwdhLhm4q5vzODSw4Xiq2ZWs03Uht%2BtbTkyIGs4i1QPB0DGBxUggBVaQRWhUFjTAZXu9Ye1LHcHAMS4eygX7rFYJotKel63uYAAvJliGYHyvAVZxPvoFiEVTP75IB4F3N47agR2Dx7ru9ZEdegwlHRzGPBx4g8eBb6m3NUr3o5ukyLxd60YxrHnvoXHBZujY6fOeWQYIMGIalFkIBh2g4ZsBHntekXlsYjnAwc66dAVJYfuJ3oZW9aLZbzR7dbGJmpRNpjjcS03zddQXboiyF%2BdZXVRpNIWoX1t2jYIQUQDmIskyzWmHZixXlchtWNa1zAdaR/Wlsjil889p0pm97BLf%2Bm3ydu5P5YZ53maLlrZULlKKpW8MzfoJZfmzP3eMDghg7hROZeF1GmSbjv%2BWjoU4%2BNAhR5xA6BtTwtwfT6GJaznO9Yn3k4QPxUu8VbBe6Jyuyd5wb0SIRkuuRIf3UwT0wuXuXHaRl3J5hPlbN/oE8pu6ukXjzf2Yxb6oHvoRX4%2BpMAeiMPCMOAcPp6hDkvAe%2B8AEzxjvPDib8ea1z6B0VgIA%2Bgrj6KQUwfQViUNQGQnQcg5ABi6D0HYgxOCUIIGQ2hWZSD/BAK4FcupXCSG4JITgIJuArBVKqFYIIVxCDIdwSh1DaGkHoX0ShCgQArFINwmhxDSBwFgEgNARg2bsDIBQCA5jLHlGAJwFYkhSBUDwJiZwOiIAOB4ZQo8tBUjzDIZw0g5iZj0AAPKayCYY0gWAjAJnYL4uJeADT5Hjjo2JhI8gq2CZQnGpC%2BghLhg4DGxB5h6CwHk/RhYjC%2BI6DQegTA2AcB4PwQQwhRAoCYTIIQeAHA6MgB0cyiRMkAFoImuDGGMgUhEJAyDkJI7RuR8gaAgOYGoWRSDmBKFEGIwRvC%2BDoJsg5oQ/C7LKC4OoKzEiFGqPoTIgh4h5FuQ0C5LQrmVCKCcuobymh7PKJwDoChWG9C4CQshFCqHJM0QSAAHCqMZKpuAjWQMgMYTjdSSDGBAXAhASCmVcNkMYegLHuOcISoFJKenSC4fUjoAjRG6hVCuOF7Y4UglcNIgAnCsTgqolF9BUaQOpTi9FqLoWQ7Ruj9H1OMTARAKBUBkqseQSgdjyUuE3JwJx2Q3EeOIF4nxsT/GBOqWErQBAomsBieo%2BJiT%2Bh2tSS84smBMnqOycgXJRT8mS0KcU/pZSKkYH6CEncdTDENLoIwFgSS2kCBcZ0sQNK%2BkDPgMMmUfhxmTOmbM/K8zZAyCWTkBIfhNDaB%2Bds7Q7z9nZBCEc/wDzaieEOYkGtgKS0uroHc9ITatnPNWUkP5kRLlPIaJW%2BoRR21XOBaC1pELyGqJhWQ%2BFiLkUZSTRizguoVi6k4DivFdVKUplJfYiS7ZJAIkYQsmQdLI0MsEZIHdkiVzcFcHClc3LkXcv5YK4VEqNFSsUDKgxvCF2SCXbEzRd6wOkHjoast3AgA%3D%3D%3D)

## 参考阅读：
[1] https://reviews.llvm.org/D63748

[2] https://quuxplusone.github.io/blog/2018/05/02/trivial-abi-101/

[3] https://quuxplusone.github.io/blog/2019/09/21/ticket-for-unique-ptr/


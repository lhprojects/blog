# unique_ptr 与 Itanium C++ ABI

这不是一篇介绍如何使用unique_ptr的文章。假定读者已经对unique_ptr**使用**和**实现**非常熟悉了。

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

现在我们总结对程序的两个负面影响

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
2. 改变abi，不能适用于std::unique_ptr，因为Itanium C++ ABI已经广泛被使用了。
3. 如果只是对unique_ptr开后门的话，那么在所有参数的临时变量中，unique_ptr是最先析构的。那么构造顺序和析构顺序就不能完全的相反。（见视频[问答环节](https://www.youtube.com/watch?v=rHIkrotSwcc) )


## ticket

std::unique_ptr作为参数传递效率不高，而raw pointer又太危险，有没有折中的方法呢？
在Itanium C++ ABI里，std::unique_ptr不能通过寄存器传递的主要阻碍是Std::unique_ptr有非trivial的析构函数。
我们可以实现一个只包含trivial析构函数的智能指针。
注意下面的代码和 [原始代码](https://quuxplusone.github.io/blog/2019/09/21/ticket-for-unique-ptr/) 有些许不同。
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
2. 表义性比raw pointer好，你知道它试图起到类似unique_ptr的作用。
3. 不需要改变ABI。
4. 易用性比raw pointer好。

但是ticket类依然有几个缺点：

1. 本质上还是raw pointer，没有任何资源管理能力. 在参数传递过程中如果发生异常，会出现资源泄露。



## 附录
完整代码见[链接](https://godbolt.org/#z:OYLghAFBqd5QCxAYwPYBMCmBRdBLAF1QCcAaPECAM1QDsCBlZAQwBtMQBGAFlICsupVs1qhkAUgBMAISnTSAZ0ztkBPHUqZa6AMKpWAVwC2tEAFZSW9ABk8tTADljAI0zEQAZk6kADqgWE6rR6hibmvv6BdLb2Tkau7l6KypiqQQwEzMQEIcamFkoqanQZWQQxji5unt4Kmdm5YQX15XaV8dVeAJSKqAbEyBwA5FIedsiGWADU4h46RphGJACes9jiAAwAgqPjk5gzc2zAJIQIRmubO9sEiz7Ct7M6E8wKClMAKpfbdcQGqlM1MgANaYAgzADssm2U1hgLwILBEC6hwAIlMsFRmAZWARZtCtnCppgAB73BGEeGIggQD5TABUPhRICmPgA%2BhAmZDZBDUVciUDQTS6ugQCADLQ8ABHAyYNk%2BAjEJ52PEedaSABsUg1rOZrI5PgAdMQUq9MMiUeIoVa%2BTC4SKxRLpbL5Yqnl81VMTVhFsjuV6wf1aFMHeLJTK5QqlXMPdgIKHScgECJgOb2aQprQcawo10uvjIbatj5iHgAG7MW4gflwumMtlozPZqP4q421vbNuSMZUTFTNlsl6iAczTvdzFtT4AJQAkgA1LYz6xsrbSGczMyyTdD0AgRXlvBsNnMZx4cRmPkXrseZRKa8T%2BzT%2BeL5ermfXqx4Kht7YAel/owPgcHyzguS4rmuG5btIO5ivuZaHqwx6nuel5FlctxGPclaYE8LxvJ83xbL8/zgiBz7gW%2BgKlghR5OhGrrENyNawvBiFsvRLpRn6szopi2K4h2hJwqS5LIJSbF0eGXGKrSDJciy7Kcpa1q8kSLHUQeUnOpGsmSUhnG6Ux2ral6epKQmJJJim5rEIa6ZNqwOaKnm/o2upnZ2qxNHsYZjEzJqqA%2BG4lYkLxED6Rx0lGQFWqamZsJWgSRJEqGCgAO7MD4nJshmdnsvmHjJXC7klV5o7Cd5WkGdFjERT52kMVGUxoLQdSxcQloeHxKSPEViXlZFfnNdqQUhUQ0aovV1VRTp/mte12qdYl3UYr1uFFT%2BlWfAyUypjSKnSAGBBBvqBbtuVAB%2BQ21dxh1TF%2BOUolg7C3Gd/UXcWNE4dW5V1uyjZZk5LabZ2vJCVtVxlqgeDoFMzhZBAKqMiitCoImmAKhD2wDpW%2B7OAYtwDlAaN2KwbSudDsPw8wABebLEMw6V%2BCqbhI/Q8kopm6NWZj4JJRpL1ggcPgQ%2BD2xU3DBhKAzTM%2BKzxDs%2BCKNtta5UI4rTJCUSCP04zzMw/QbNa6DOzi9cFu4wQ%2BOE3KHIQKTtDk/YlMw3DuuzU1smhsNbpzCqayozzgwKv6ZVm%2BhEtu1M0tyr7is%2B7dfs6AHnpa2DxWwhrnKGvtFra3CHvx/GBCiiASxlmmeZi5HlvHtbpYE0T9uO87mCu9THs3XNUY0t3XvRin9CB9zGOhwLYO11D0ex2y/cydk020TVPfJ6n2CAvmGcadnBC50i1emzrdNzw1K8D8KpdihX5oEIfBKfVtVs283JOG23HfuyfgpIj/qpD6qDed9R683Hmrba2IiCshWuiPe3pMC%2BkKg/c209qazz/hFBEQplTD09HfVWmcpiQNQNA3igJjSYB9EYZEBcs6IyNHne%2BO9v5YKRKGG%2BykkGq1rkMHorAQBDDMEMUgpghgbGEagAROg5ByBDH0AYBxRicGEQQAR4i8ykGBJ4MwhoPCSG4JITgEJuAbA1JqDYEILD8KGNwYRojxGkEkUMYRCgQAbFIKosRvDSBwFgEgNAWE8DsDIBQCAAT5bBJAMATgGxJCkCoEE24xBXEQGcGo4Rp5aBZGWAI5RpAAkLHoAAeSdjkrxpAsBGBTOwdJFS8AmjSJXVx5TSSpFtrk4RrNrF5PJs4RmxBlh6CwB0jxpYjDpJ6DQegTA2AcB4PwQQwhRAoBkTIIQeBnCuMgD0IKxQ2oCIALRFI8FMA5IpeISBkHIIxLiUhpA0BAKwjRTBGMsNoCocQEieAABwRACHs55XAIR/KiLQD5VREi/MKKkPZpQGj6DyEC5IRR0gtHBR0SFigWiAteXUMo6KvkeG%2BT0BQ8jBhcD4QIoRIjalOJJN8jUByNTcD2sgZAUwYmGkkFMCAuBCAkACkkKYehAnBMFZwFE0irkyBURMnoWi9GGg1GYb53ZvkQg8CYgAnBsTgmohACNsaQcZMT3H2IkQIlxbiPETJ8TARAKBUCircOQSg4SgnVB3JwGJ3gEm4jcCktJ5TMnZJGQUrQBASmsDKQ4yp1ThixvqTC8smBmkONacgdpQw8ldJGb0/pgyMDDDyfucZXjJl0EYCwGp8yBBxKWWIVZ8helbORI4hUQRmlHJOWc0uFym03ORcmh5TyEVhG8FYAl1RuAeBBQCsdLy51BCne4GdQ77m0DhTkBdghoUbq3SuzwwK8XwtCIuk9rRYgQqPSSslczKWCLsbSgR9LGXMpag2jlnBDQbENJwHlfKJriozCKiJbhBWSElU22V5b5WeEkD%2BoxZgZ3fLMFq5lWq9UGpsU%2B8pTirXuM8eoh9khcMOPwza2DpBK7JKCCAbgQA)

## 参考阅读：
[1] https://reviews.llvm.org/D63748

[2] https://quuxplusone.github.io/blog/2018/05/02/trivial-abi-101/




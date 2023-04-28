
# 单例模式

单例模式是很常用的设计模式。现在我们要研究一下如何实现**线程安全高效**的单例模式。
我们不研究各种单例模式的变体，我们只研究简单单例模式。

## 单线程单例模式

假设我们有一个`Manager`类，我们要实现一个`Manager`单例，通过`GetManager`得到这个单例。
```c++
// .h
struct Manager {
    Manager(std::string name) : name(std::move(name)) {
    }
    std::string name;
};
Manager &GetManager();
```
单线程单例模式实现起来特别简单。我们定义一个**函数静态变量**变量来存储单例。
在第一次调用`GetManager`的时候，我们对单例模式进行初始化。
```c++
// .cpp
Manager &GetManager_Meyers() {
    static Manager manager("Harry");
    return manager;
}
```
上面的代码等价于
```c++
// .cpp
Manager &GetManager_Meyers() {
    static char buffer[sizeof(Manager)]; //align as Manager
    static char init;
    if(!init) {
        new(buffer) Manager();
        init = true;
    }
    return manager;
}
```
为了验证我们观点，我们对代码进行了反汇编。
```asm
GetManager_Meyers():
        movzx   eax, BYTE PTR guard variable for GetManager_Meyers()::manager[rip]
        test    al, al
        je      .L69
        mov     eax, OFFSET FLAT:GetManager_Meyers()::manager
        ret
```
其中`guard variable for GetManager_Meyers()::manager`就是我们的`init`变量。

如果我们要求，不是在第一次调用`GetManager`的时候初始化`Manager`单例，而是进入`main`函数之前就初始化。那么我们可以使用**全局变量**，而不是函数静态变量。

```c++
Manager manager("Harry");
Manager &GetManager_Global() {
    return manager;
}
```
后者的`GetManager`应该会更快一点，后者不需要检测变量是否单例已经初始化，因为我们总是假定单例已经初始化。其生成的代码最为简洁和高效：
```asm
GetManager_Global():
        mov     eax, OFFSET FLAT:global_manager
        ret
```

## Mutex 单例
为了实现线程安全，我们可以对初始化过程加锁
```c++
std::mutex mutex;
Manager &GetManager_Mutex() {    
    static Manager *manager; // initialize to zero
    std::lock_guard<std::mutex> guard(mutex);
    if(!manager) {
        manager = new Manager("Harry");
    }
    return *manager;
}
```
除了性能有问题其他问题都没有。

## std::once_flag 单例

使用`std::once_flag`也可以实现单例。
```c++
Manager &GetManager_OnceFlag() {
    static Manager *manager;
    static std::once_flag flag;
    std::call_once(flag, [&](){
        manager = new Manager("Harry");
    });
    return *manager;
}
```
其中`static std::once_flag flag;`会对`flag`进行zero-initialization，初始化完成后的状态表示`call_once`还没有调用过。这是在**程序加载**时候完成的，所以一定是线程安全的。

第一次调用`call_once`，`call_once`会调用lambda表达式对`manager`进行初始化，同时会更改`flag`的状态，表示`call_once`已经被调用过了。后续的对`call_once`调用，就不会再调用lambda表达式。最终的效果是`manager`只被初始化一次。这一切都是线程安全的。


## Meyers 单例

根据c++11对static新规定，函数静态变量的初始化是线程安全的。这意味如下这种写法，实际上是线程安全的，这和单线程单例模式没有一点区别。
```c++
Manager &GetManager_Meyers() {
    static Manager manager("Harry");
    return manager;
}
```
这种单例的实现方法又称为Meyers单例。

## Atomic单例

使用原子变量也可以实现单例模式，这就是最常见的double-check算法

```c++
static std::atomic<Manager*> atomic_manager;
static std::mutex atomic_mutex;
Manager *GetManager_Atomic() {

    Manager *ptr = atomic_manager.load(std::memory_order_acquire);
    if(!ptr) [[unlikely]] {        
        std::lock_guard<std::mutex> guard(atomic_mutex);
        ptr =  atomic_manager.load(std::memory_order_relaxed);
        if(!ptr) {
            ptr = new Manager("Harry");
            atomic_manager.store(ptr, std::memory_order_release);
        }
    }
    return ptr;
}
```

除了第一次调用`GetManager`，其余大多数调用`manager.load(std::memory_order_acquire)`都会返回一个非空指针。而指针一旦非空，那么就可以快速结束函数调用了。在`x86-64`平台上，`manager.load(std::memory_order_acquire)`只是一个不带锁的内存读取指令（`mov`）。其反汇编代码如下

```
GetManager_Atomic():
        push    r12
        push    rbp
        push    rbx
        sub     rsp, 32
        mov     r12, QWORD PTR atomic_manager[rip]
        test    r12, r12
        je      .L94
.L71:
        add     rsp, 32
        mov     rax, r12
        pop     rbx
        pop     rbp
        pop     r12
        ret
.L94:
        ...
```
也就是说对于`GetManager`的绝大数调用，有意义的工作是一次内存读取，一次比较，一次条件跳转和一次返回指令。

## 更快的Atomic单例

上面的单例模式已经更迅速，但是上面的单例模式没有生成最优化的代码。因为`if(!ptr)`后面有大段的初始化代码，编译器必须为这些代码，做相当多的准备工作。所以我们把初始化代码写在另外的函数，这还优化了CPU的pipline，减小了CPU指令的的缓存压力。
```c++
static std::atomic<Manager*> manager;
static std::mutex mutex;

__attribute__((noinline))
Manager *GetManager_Atomic();

Manager *GetManager_Atomic2() {
    Manager *ptr = atomic_manager.load(std::memory_order_acquire);
    if(!ptr) [[unlikely]] {   
        ptr = GetManager_Atomic();
    }
    return ptr;
}
```

其反汇编代码如下：
```c++
GetManager_Atomic2():
        mov     rax, QWORD PTR atomic_manager[rip]
        test    rax, rax
        je      .L100
        ret
.L100:
        jmp     GetManager_Atomic()
```
也就是说对于`GetManager_Atomic2`的绝大数调用，只需要指令一次内存读取，一次比较，一次条件跳转和一次返回指令。这比Meyers单例还要高效。因为在`Meyers`单例里，我们的标志位只是起到了标志位的作用，我们读取单例的地址还需要额外的一次`mov`指令。而在`GetManager_Atomic2`里，我们可以使用空指针作为单例未初始化的标志，从而精简了指令，提高了效率。

# Benchmark
Benchmark 的实现参见 https://gist.github.com/lhprojects/5dc9d4a30eb4ee8dc9caf7ab47b85707 。
Benchmark实现了本文提到的所有单例，但是Benchmark里边的命名规则和本文中的例子不一样。但是读者依然可以从名字中看出来其单例模式实现的方法。

```
----------------------------------------------------------------
Benchmark                         Time           CPU Iterations
----------------------------------------------------------------
BM_global                       309 ns        308 ns    2292985     全局变量单例
BM_static                      1807 ns       1801 ns     381038     静态变量单例
BM_once                        3634 ns       3632 ns     195386     std::once_flag
BM_atomic                      2135 ns       2134 ns     331749     原子单例
BM_atomic_init_no_inline       1516 ns       1515 ns     424253     原子单例（初始化代码在其他函数）
BM_mutex                      19354 ns      19339 ns      35721     锁单例
```

我们看到

- 最快的全局变量单例。但是全局变量单例的初始化是在`main`函数之前。
- 最慢的是`Mutex`单例。锁是重量级的！
- 第一次调用时初始化的单例模式中，最快的是`原子单例（初始化代码在其他函数）`。





完整汇编代码请见
https://godbolt.org/#z:OYLghAFBqd5QCxAYwPYBMCmBRdBLAF1QCcAaPECAM1QDsCBlZAQwBtMQBGAFlICsupVs1qhkAUgBMAISnTSAZ0ztkBPHUqZa6AMKpWAVwC2tQVvQAZPLUwA5YwCNMxLp1IAHVAsLraewyaCnt5qdFY29kZOLpxuSiqhtAwEzMQE/samccqYqr7JqQThdo7OroopaRmBcZVF1iVRZbEAlIqoBsTIHADkUgDM1siGWADU4v06BAjEmMzoE9jiAAwAggNDI5jjk0YGBJgAHosr65KDtMMGYxM6zERGeBL9S2unAPTvowB0CKcKBGIBlUowAsiJmMBnOMAOyyNajRFgiFQ4gQAHoEAgAHEazAUa0ZhGTAtUYgAlEzDogiYkBGVAANyphOJLVJ4jhpyRsIAIlykRisTi8RTiRN4esYXz%2BhKPl9vsh3O5TuDCajxpIAGwAcUwBFVkOcAH0CmpkBB2ZyEQKUmbkWroUYUc4IFJJAAJVLEACebpa4v5iNmBE6tFGTodxADbylpxVzuIo2ArFQDjYRojhrRbs9xB9fujqwN6qkOr1xeN2pTadYFthEu5wdDSer6czqMLHL5bzWgrp%2ByO4YHxxl8cjGrL%2BoTRtBw7rHOk3MDowB9ye9qzowAVO3nOLRp9RtYfGw8AAvbZEUYX4ioZd9lPIADWRuABlSC0mfb2BxH2CT77EOgEA/kc/qjtaiJ4FQEBgGAu7EJaDbckiCE7DyBKYAA7huqKupIHper6BHgchiJdsuTbEGGO4Jp2sY9kWCYTrqU6RkaADylyYAAYsIwDzlaqzcqudoVomtGRoWIm2uufZ0N0RpUPxozKZC0k2rSLCsKwRoKVSanAKQ4wAKyyFq4gmTyFoLsu3JoRMGE2Dh4n4YRebEZIpHLl23mQaMVE0Qh9HdusaziSx5bTqCmDes4CiCWRK6ycguGOgmbm5vmJEaUGerNsFEGSqF/wpcltL3KgjzPDo4lbosoyVdVGZ0UVolyTSWKgYcjUPE8GbDoWEVbqx4lGqsfXmkhcb%2BcN7iAuhvVVf1CHfCm8zUrSxL0j6elAcazDIAAjgYeCzH5wlItBsFgPNiGmbIZkGLQrB4E%2Byi%2BlZlkYQuKFInZmlYo%2BL5vh%2BtzfoNLwAR%2BEBNStw4XX9iJ3YtS3Nat63Ad%2BmA7d6e1YMQRqzMIhyYOgiNI9dcF3dN/lI6MKOOZhLkZTmREFkV9PcnDyAtZG3wAiQVJ3cZ2O4/jxrE3MSgU39FH%2BfLl15SG1EM4CIUzWFTHjiNUXsRNy3IJIiXLnNC1MzzfNZmtqAbWLJB4yQBNGodJ1nSSuVHjB1OAuyZmWdIz2ve9rCfXyVn1v9dNIoz/QYaN04G9VNmc/9DFKwF%2BWq3dGuMT0bSsCAPQmT0pCmD0yyl6gRc6HIcgrh0XTbAMnClwQReV2ypBPiA3AAJzfP0PDLDCffcAR/QABxajCmpCEX3Cl%2BXlekNXPSlwoIDLKQ7cV/npBwLASBoEY7h4OwZAUBAJ9nxfIDAAohLuAoCCoAQpBUOfBzEJvEAOB3pcHDWFSN6IurdSAn2JPQLiocAGkCwBGZMvQV74FmHkJkm896kCOLkAcYDS7WAOIXLBr0HDEBAXoLAcDAR4CMPgtoNB6BMDYBwHg/BBDCFECgOuMghB4AcJvSAbRUDzV8JggAtBxSQoxxEYkchIGQchOBng3jkPIGgIDmGqFkbB2hiiRGiEELwPg6DaKMSEXw%2BjSgxEUGoxIBQqj6EyIIeIuR7F1CsU0Gxq5HEBB0T4%2BoERrFcDaAoRu3QQnz2LkvOBa9DiT01OIzU3AkzIFShAQEz0nykggLgQgJANRD2MnoU%2B59oQt1JLXRRMg24AK7j3EyyxviakniZPukhlgmRhLPTgMJ%2BiSF4MQxeZdYlFw3lvHedSC5F0kDErBa9al7y7kyH%2Bvhe5AA




















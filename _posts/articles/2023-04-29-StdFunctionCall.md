---
title: Is C++ std::function slow?
tags: [c++, "std::function"]
categories: [Programing, c++]
---

# std::function
这**不是**一篇介绍如何使用std::function的文章。我们假定读者对`std::function`已经非常熟悉了。在这篇文章里我们要深入的研究一下`std::function`函数调用`operator()`的性能。我们将通过三个案例，来研究调用std::function时的性能。

本文全部的代码可以从 https://gist.github.com/lhprojects/d06145efb0f9728dcd0a41d6bdb881a8 找到。（No，网断了，所以代码丢失了！只剩了最后一小坨。）


# 案例1 - 传入整数

## 设定

我们研究一种典型的情况：function从一个lambda表达式构造，而lambda表达式只捕获了一个对象的引用（指针），在lambda表达式里，我们使用了这个对象的成员数据。代码如下
```c++
class struct Clss {
    int c = 0;
    virtual int virtual_function(int a) {
        return a + c;
    }
};

int main() {
    Clss obj;
    std::function<int(int, int)> f = [&](int a, int b) {
        return obj.c + a;
    };
    
    // ...
}
```
为了方便反汇编，我们写了一个单独的函数`invoke_stdfunction`来，来调用`f`：
```c++
#ifdef _MSC_VER
__declspec(noinline)
#else
__attribute((__noline__))
#endif
int invoke_stdfunction(std::function<int(int, int)>& f)
{
    return f(1);
}
```
在函数里，我们使用了MSVC的特有拓展`__declspec(noinline)`和GCC的特有拓展`__attribute((__noline__))`，它们可以阻止编译器内联函数。这样可以避免编译器做实际生产环境中不可能做的优化，例如虚函数编译期解析和绑定。

作为对比，我们还写了一段不使用`std::function`而是使用虚函数的的函数`invoke_virtual`达到同样的效果。
```c++
#ifdef _MSC_VER
__declspec(noinline)
#else
__attribute((__noline__))
#endif
    int invoke_virtual(Clss* object)
{
    if (!object) {
        exit(1);
    }
    return object->virtual_function(1);
}
```
对于`std::function`，如果其内容为空，那么函数调用就会抛出异常。在`invoke_virtual`中，我们对对象指针是否为`null`也做了一个判断：如果指针为`null`，我们就立即退出程序。这样的判断在生产环境中通常也是需要的（当然不会这么处理）。所以对`invoke_stdfunction`和`invoke_virtual`的对比，会是一个公平的比较。

另外对于GCC，如果虚函数没有被覆写，那么就会针对其生成特别的优化的代码。这不是实际生产环境的情况，为此，我们写了`Clss`的子类`Clss2`，并且覆写了`invoke_virtual`方法。

## 反汇编

我们采用了GCC 9.2和VS2019对样例进行编译，目标平台设定为x86-amd64。MSVC和GCC的实现有基本的不同，MSVC使用了虚函数来实现类型擦除，对于我们研究的这种情形，最终生成的代码和调用虚函数是几乎一样的（除了多一次载入内存）。个人更喜欢MSVC的实现，我们会另外写文章讨论。这篇文章只讨论GCC，也只展示GCC 9.2的反汇编结果。现在我们把两个函数反汇编分别摘抄如下

```asm
invoke_stdfunction(std::function<int (int)>&):
  sub rsp, 24                # 申请栈内存
  cmp QWORD PTR [rdi+16], 0  # function对象是否为空
  mov DWORD PTR [rsp+12], 1  # 1 入栈
  je .L12                    # throw expection
  lea rsi, [rsp+12]          # 1 的地址
  call [QWORD PTR [rdi+24]]  # _M_invoke
  add rsp, 24                # 释放栈内存
  ret
.L12:
  call std::__throw_bad_function_call()

std::_Function_handler<int (int), main::{lambda(int)#1}>::_M_invoke(std::_Any_data const&, int&&):
  mov rdx, QWORD PTR [rdi]   # 载入`object`指针
  mov eax, DWORD PTR [rsi]   # 取出参数 1
  add eax, DWORD PTR [rdx+8] # 取出成员 `c` 并且加1
  ret
```

```asm
invoke_virtual(Clss*):
  test rdi, rdi              # 指针是否为空
  je .L18                    # exit
  mov rax, QWORD PTR [rdi]   # 载入虚函数表指针
  mov esi, 1                 # 1 保存到寄存器
  mov rax, QWORD PTR [rax]   # 载入虚函数`virtual_function`
  jmp rax                    # 调用虚函数
.L18:
  push rax
  mov edi, 1
  call exit
```

我们总结一下两者的差别

- `invoke_stdfunction`首先需要从指向`std::function<int (int, int)>`的指针`rdi`加上偏移量`12`读取一个指针。根据这个指针来判断`std::function`是否为空。而`invoke_virtual`只需要直接判断`rdi`是否为空，便可以判断`object`是否为空。后者省去了一次内存读取。后者之所以能节省一次对内存的读取，是因为对象的指针`object`作为参数正好已经在寄存器中了。但是这种对优化不总是可行，例如

    - 载入类的成员函数，例如
     ```c++
     if(this->object) this->object->virtual_function(1, 1);
     ```
    - 指针是栈中的变量，但是函数体很长，指针被挤兑到栈中，例如
    ```c++
    Clss *object = ...;
    // lots of codes
    object->virtual_function(1,1,);
    ```
    - 指针是栈中的参数，但是函数体很长，指针被挤兑到栈中，例如
    ```c++
    void foo(Clss *object) {
        // lots of codes
        object->virtual_function(1,1,);
    }
    ```

- 为了调用虚函数`virtual_function`，`invoke_virtual`需要首先读取`object`的虚函数表地址`[edi]`，然后再从虚函数表中读取虚函数的地址`[rax]`。然后把参数存入寄存器，此时`invoke_virtual`就可以直接调用虚函数了。

- 而为了调用函数`virtual_function`，`invoke_stdfunction`则需要两步：

   - 第一步，从指向`std::function<int (int, int)>`的指针`rdi`加上偏移量`24`读取一个函数指针。同时将`std::function`的参数压入到栈中，然后将参数的地址保存在寄存器中。另外一个隐藏的参数是指向`std::function`的指针`rdi`。

   - 第二步，转到这个函数指针。结合`main`函数的反汇编的上下文，就可以知道这个函数实际上是`_Function_handler::_M_invoke`。在这个函数里，我们通过参数的地址，将参数读取到寄存器中。

可见`std::function`参数传递更为复杂。为了擦除类型，必须存在一个中间函数`_M_invoke`。对于`std::function`不同的底层情况（lambda表达式，函数指针等等），`_M_invoke`实现也不一样。对于我们的现在的情况，伪代码如下（真实代码见 https://github.com/gcc-mirror/gcc/blob/master/libstdc%2B%2B-v3/include/bits/std_function.h）

```c++
struct LambdaType {
    Clss &obj;
    // step 3
    int operator(int a) {
        return obj.c + a;
    }
};

struct _Function_handler {
    // step 2
    // 万事不决用引用
    static int _M_invoke(_Any_data &data, int &&a) {
        // 恢复底层类型信息
        return data.lambda(std::move(a));
    }
};
struct function {
    
    union _Any_data {
        LambdaType lambda;
        // ...
    } data;

    
    // 底层类型已经被擦除。
    void *_M_manager;
    int (*_M_invoker)(_Any_data &data, int &&) = _Function_handler::_M_invoke;
    
    
    bool empty() { return _M_manager != nullptr; }
    
    // step 1
    // 函数签名必须为int(int)。
    int operator()(int a) {
        if(empty())
            throw ...;           
        return _M_invoker(data, std::move(a));
    }
};

```

我们可以看到，`_M_invoke`接受的参数是引用(`&&`)而不是值。这导致`std::function::operator()`的参数只能首先压入栈中，然后把其地址传递到`_M_invoke`。好处是对于大型对象，我们可以节省一次复制或者移动。坏处是对于像整数这类体积很小的类型，无法通过寄存器传递到`_M_invoke`。 注意，读者完全不必担心`data.lambda(std::move(a))`，实际上，这个语句完全被编译器内联掉了。

实际上一个更仔细的实现，应该对整型或者指针进行特殊处理，将`_M_invoke`的签名改为`int(int)`，这样只需要载入`object`指针，不需要将参数推入栈中然后再从栈中去读这样低效了。

- 最后，我们发现`invoke_stdfunction`对进行了栈指针的移动，而`invoke_virtual`不需要移动栈指针。所以`invoke_virtual`生成的指令更高效了。但是，这也不是普遍情况。因为栈指针可能会因为别的局部变量，而必须进行移动，从而和`invoke_stdfunction`一样生成两个指令来修改和恢复栈指针。

## 性能测试

我们的`virtual_function`函数体非常的轻量级，所以时间主要是函数调用的开销。我们测试了`std::function`和单纯虚函数调用的性能。代码分别为
```c++
...
{
    volatile std::function<int(int, int)>* p = &f;
    printf("%p\n", (void*)&p);
    auto t0 = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < 1000'000'000; ++i) {
        (*(std::function<int(int, int)>*)p)(1, 1);
    }
    auto t1 = std::chrono::high_resolution_clock::now();
    auto nano = std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0);
    std::cout << nano.count() << std::endl;
}

{
    volatile Clss* p = &v;
    printf("%p\n", (void*)&p);
    auto t0 = std::chrono::high_resolution_clock::now();
    for (int i = 0; i < 1000'000'000; ++i) {
        ((Clss*)p)->virtual_function(1, 1);
    }
    auto t1 = std::chrono::high_resolution_clock::now();
    auto nano = std::chrono::duration_cast<std::chrono::nanoseconds>(t1 - t0);
    std::cout << nano.count() << std::endl;
}
...
```
我们使用了`volatile`关键字，这样编译器无法假定每次从`volatile`修饰的指针读取的内容是一样的。这样我们可以通过一段简短的代码一定程度上模拟真实的情况。对于`std::function`和虚函数调用，我们分别运行了1E9次，总时间分别为1.52秒和1.46秒。差别很小，不是吗？

# 案例2  - 传入指针
我们经常需要传递类型为指针的参数，现在我们把`std::function`的参数改为指针，看看有什么情况。

## 设定
```c++
using namespace std;
struct Clss {
    int c = 0;
    virtual int virtual_function(Clss* ref)
    {
        return c + ref->c;
    }
};
...noinline... int invoke_stdfunction(std::function<int(Clss*)>& f, Clss *ref)
{
    return f(ref);
}

...noinline... int invoke_virtual(Clss* object, Clss* ref)
{
    if (!object) {
        exit(1);
    }
    return object->virtual_function(ref);
}
int main()
{
    Clss obj;
    std::function<int(Clss*)> f = [&](Clss* ref) {
        return obj.c + ref->c;
    };
    invoke_stdfunction(f, &obj);
    invoke_virtual(&obj, &obj);
    // ...
}
```
相应的反汇编的代码如下
```asm
invoke_stdfunction(std::function<int (Clss*)>&, Clss*):
  sub rsp, 24
  cmp QWORD PTR [rdi+16], 0
  mov QWORD PTR [rsp+8], rsi
  je .L12
  lea rsi, [rsp+8]
  call [QWORD PTR [rdi+24]]
  add rsp, 24
  ret
.L12:
  call std::__throw_bad_function_call()

std::_Function_handler<int (Clss*), main::{lambda(Clss*)#1}>::_M_invoke(std::_Any_data const&, Clss*&&):
  mov rdx, QWORD PTR [rdi]
  mov rax, QWORD PTR [rsi]
  mov eax, DWORD PTR [rax+8]
  add eax, DWORD PTR [rdx+8]
  ret

invoke_virtual(Clss*, Clss*):
  test rdi, rdi
  je .L18
  mov rax, QWORD PTR [rdi]
  jmp [QWORD PTR [rax]]
.L18:
  push rax
  mov edi, 1
  call exit

Clss::virtual_function(Clss*):
  mov eax, DWORD PTR [rsi+8]
  add eax, DWORD PTR [rdi+8]
  ret
```

- 第一次跳转之后，`invoke_stdfunction`到达`_M_invoke`而`invoke_virtual`到达`virtual_function`。

- `invoke_stdfunction`中，仍然需要首先将指针`ref`压入栈，然后把其地址传递给`_M_invoke`。

- `_M_invoke`为了取出`ref->c`需要两次内存访问，首先根据传入的`ref`的地址取出指针`ref`，然后根据指针`ref`取出`c`，一共两次内存访问。

- `_M_invoke`为了取出lambda表达式捕获的`obj.c`，也需要两次内存访问。是因为传入`_M_invoke`的隐藏指针`this`是指向`std::function`的，同时也是指向`lambda`表达式对象的。我们首先需要取出指向`obj`的指针，也就是lambda表达式的数据成员；然后根据这个指针取出`c`。

## 性能测试
们测试了`std::function`和单纯虚函数调用的性能。对于`std::function`和虚函数调用，我们分别运行了1E9次，总时间分别为1.53秒和1.45秒。

# 案例2  - 传入引用

## 设定

我们已经知道，`_M_invoke`的参数是引用类型的了。如果`std::function`的函数签名是值类型的，我们需要将值入栈，然后把引用传递给`_M_invoke`。所以将指针改为引用是否能够提升性能呢？我们修改代码如下：

```c++
struct Clss {
    int c = 0;
    virtual int virtual_function(Clss& ref)
    {
        return c + ref.c;
    }
};
...noline... int invoke_stdfunction(std::function<int(Clss&)>& f, Clss &ref)
{
    return f(ref);
}
...noline... int invoke_virtual(Clss* object, Clss& ref)
{
    if (!object) {
        exit(1);
    }
    return object->virtual_function(ref);
}
int main()
{
    Clss obj;
    std::function<int(Clss&)> f = [&](Clss& ref) {
        return obj.c + ref.c;
    };
    invoke_stdfunction(f, obj);
    invoke_virtual(&obj, obj);
    return 0;
}
```
相应的反汇编的代码如下
```asm
invoke_stdfunction(std::function<int (Clss&)>&, Clss&):
  cmp QWORD PTR [rdi+16], 0
  je .L14
  jmp [QWORD PTR [rdi+24]]
.L14:
  push rax
  call std::__throw_bad_function_call()
  
std::_Function_handler<int (Clss&), main::{lambda(Clss&)#1}>::_M_invoke(std::_Any_data const&, Clss&):
  mov rdx, QWORD PTR [rdi]
  mov eax, DWORD PTR [rsi+8]
  add eax, DWORD PTR [rdx+8]
  ret


invoke_virtual(Clss*, Clss&):
  test rdi, rdi
  je .L20
  mov rax, QWORD PTR [rdi]
  jmp [QWORD PTR [rax]]
.L20:
  push rax
  mov edi, 1
  call exit

Clss::virtual_function(Clss&):
  mov eax, DWORD PTR [rsi+8]
  add eax, DWORD PTR [rdi+8]
  ret
```

- 首先在第一次跳转之前，`invoke_stdfunction`的代码要更加简洁，它只需要两次顺序无关的内存访问。而`invoke_virtual`也需要两次内存访问，但是两个指令必须按照顺序执行。这个差别很小。

- 第一次跳转之后，`invoke_stdfunction`到达`_M_invoke`而`invoke_virtual`到达`virtual_function`。`_M_invoke`比`virtual_function`多一次内存访问。这是因为传入`_M_invoke`的隐藏指针`this`是指向`std::function`的，同时也是指向`lambda`表达式对象的。我们首先需要取出lambda表达式的数据成员，即指向`obj`的指针。而对于`virtual_function`来说，`this`指针就是指向`object`的指针，就是指向`obj`的。

- 由于不许将参数入栈，`invoke_stdfunction`也省略了对栈指针的修改和恢复。

## 性能测试

们测试了`std::function`和单纯虚函数调用的性能。对于`std::function`和虚函数调用，我们分别运行了1E9次，总时间分别为1.55秒和1.47秒。传递指针和传递引用的性能几乎相同！


# 总结

- std::function对函数是否为空的的运行时判定是强制的；而采用虚函数的话，对对象是否为空的判定，是用户自己决定的。

- 如果函数参数是值类型的：那么调用std::function时需要将参数压入栈中，然后传递参数时，传递的是参数的地址。由于需要将参数入栈，所以除了本身的开销外，可能会对其他优化产生略微的负面影响，例如无法省去对栈指针的移动。

- 虚函数和`std::function`性能几乎是相同的。



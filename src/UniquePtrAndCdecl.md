# unique_ptr 与 cdecl

这不是一篇介绍如何使用unique_ptr的文章。假定读者已经对unique_ptr**使用**和**实现**非常熟悉了。

最近看了这个[视频](https://www.youtube.com/watch?v=rHIkrotSwcc) ，然后自己再收集了一些资料，有些感悟记录如下。

## cdecl 调用约定

考虑如下的代码
```c++
void foo(unique_ptr<int> t);
void bar() {
    unique_ptr<int> p(new int);
    foo(std::move(p));
}
```
考虑一个问题，调用foo的时候，参数是如何传递进去的？
GCC通常使用cdecl调用约定。
在cdecl调用约定里，对于non-trivial的pass-by-value参数，我们首先会在**栈**中创建一个临时变量，
然后把临时变量的地址传递给被调用的函数，
函数调用完毕后，调用者再清理临时变量（包括调用析构函数）。

所以上边的代码就类似于
```c++
void foo(unique_ptr<int> *pt);
void bar() {
    unique_ptr<int> p(new int);
    unique_ptr<int> t = std::move(p);
    foo(&t);
    t.~unique_ptr<int>();
}
```
这种调用者负责清理临时变量的做法，使得这种调用约定没有真正的move语义。
这会给程序带来负面的影响。
上面的代码中，注意，我们把`t`的地址传递给了`foo`。
如果`foo`把`t`移动到了别的地方，那么`bar`运行` t.~unique_ptr<int>()`时候，就不应该去释放内存。
如果`foo`没有动`t`，那么`bar`运行`t.~unique_ptr<int>()`时候，就应该释放资源。但是调用者根本不知道`foo`是否真的消化了这个unique_ptr，所b以`t.~unique_ptr<int>()`无法被优化掉。只能老老实实的生成如下的代码
```c++
if(t.raw_ptr) delete t.raw_ptr;
```

具体的反汇编代码证明这种推断。详细见 [反汇编](MyCompilerExplorerSnipets.html)。我们摘抄关键反汇编代码如下
```asm
foo():
  sub rsp, 24
  mov edi, 4
  call operator new(unsigned long)
  lea rdi, [rsp+8]
  mov QWORD PTR [rsp+8], rax
  call consume_unique_ptr(std::unique_ptr<int, std::default_delete<int> >)
  mov rdi, QWORD PTR [rsp+8]
  test rdi, rdi
  je .L1
  mov esi, 4
  call operator delete(void*, unsigned long)
.L1:
  add rsp, 24
  ret
```

现在我们总结对程序的两个负面影响

- unique_ptr必须通过压栈，再传递地址的方式来传递参数。被调用的函数要访问unique_ptr中的原始指针，多了一个间接层。

- 调用者清理临时unique_ptr，但是调用者不知道被调用者如何蹂躏了这个临时变量，所以调用者无法做出足够的优化。

## 想象的调用约定


- 第一，unique_ptr本身（它本身的全部就是一个原始指针）必须通过寄存器传递。

- 第二，被调用者清理临时变量。（类似于`stdcall`）。下面我们来讨论一下被调用者清理临时变量的好处。
考虑如下代码：
```c++

// 情况 1
void foo(unique_ptr<int> t) {
    t->...
    // 需要为释放t的资源
    // 析构函数变为
    // delete t.raw_ptr;
}

// 情况 2
void foo(unique_ptr<int> t) {
    ... = std::move(t);
    // t被掏空了，不需要再析构了
    // 析构函数变为
    // assert(t.raw_ptr == nullptr)
}

// 情况 3
void foo(unique_ptr<int> t) {
    if(t->....) {
        std::move(t);
    }
    ...    
    // 做一个动态判断
    // 析构函数变为
    // if(t.raw_ptr) delete r.raw_ptr;
}

void bar() {
    unique_ptr<int> p(new int);
    foo(std::move(p));
}
```
我们有三中情况的`foo`，第一种情况的`foo`需要释放`t`的资源。第二种情况的`foo`不需要释放`t`的资源。第三种情况的`foo`需要做一些动态判断。
第三种情况的`foo`最复杂，但是可能是最少遇到的情况。
所以由被调用者负责析构函数的优势就很明显了，只有被调用者熟悉参数需要析构时候是什么状态，以根据不同情况做相应的优化。
[有人](https://reviews.llvm.org/D63748) 就给clang/llvm提出patch，来实现这种想象的调用约定。
但是由被调用者负责析构函数也具有[问题](https://www.youtube.com/watch?v=rHIkrotSwcc)。 
例如，如果只是对unique_ptr开后门的话，那么在所有参数的临时变量中，unique_ptr是最先析构的。那么构造顺序和析构顺序就不能完全的相反。






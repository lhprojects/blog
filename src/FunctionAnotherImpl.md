# std::function with Effective Small Buffer Optimization

对比GCC和MSVC的实现，一时手痒，自己实现了一个`std::function`的另外一种设计`esbo::function`。
代码详见 https://gist.github.com/lhprojects/70c8414f9579a6a2d577a0bbf79934a4 。
和GCC以及MSVC的主要区别是：**`esbo::function`对象除了一个指针，其余部分全部用作buffer**。GCC和MSVC一般需要两个指针来关系函数对象。
所以我自己称为std::function with Effective Small Buffer Optimization，有效主要体现在对空间的优化上。
另外一个优化是，对于整数，浮点或者指针类型，通过传值来传递参数更加有效。我们针对此做了优化。详细见代码`smart_forward`。
在我们的测试中，确实发现此项优化，对于传递两个整数的情况，确实有大概10%的性能改进。
在MSVC和GCC的实现中也很容易完成这个优化。但是GCC和MSVC都没有做，可能是因为收益不大。

目前还是原型阶段，大部分成员函数已经实现了。未完成的工作主要是需要写测试保证没有bug。不太有时间写原理，补上一个性能对比图吧。


# 性能测试


![benchmark](./FunctionAnotherImpl/bench.png)

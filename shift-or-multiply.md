
# 移位or乘法
今天在面试c++的时候，把向右移位8位写成了`*256`，我辩解说编译器可以把`*256`优化为`<<8`。
但是真的会这样吗？我用Visual Studio 2017进行了实验。结果如下
```
a = a * 256;
009A17D0  mov         eax,dword ptr [a]  
009A17D3  shl         eax,8  
009A17D6  mov         dword ptr [a],eax  
```
可见，果然如此。

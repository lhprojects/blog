# 翻译 XGBoost

[Introduction to Boosted Trees](https://xgboost.readthedocs.io/en/latest/tutorials/model.html)


XGBoost表示Extreme Gradient Boosting，
这里术语`Gradient Boosting` 起源于Friedman的论文`Greedy Function Approximation: A Gradient Boosting Machine`. 
这是一篇关于gradient boosted tree教程，大部分内容都是基于Tianqi Chen的幻灯片，他是XGBoost原始作者。

gradient boosted tree已经存在一段时间了，已经存在这个话题大量的话题。
在这这篇教程里，我们介绍了监督学习的基本原理，并且尽量把所有相关内容都包含进来。
我们这样解释会更加清晰，更加正式，并且简洁阐述清XGBoost的模型。

# 监督学习的基本原理
XGBoost是用来解决监督学习问题的。在监督学习里，我们使用训练样本（有很多特征）x_i来预测我们目标变量y_i。
在我们学习树是什么之前，我们来看看监督学习的基本原理

## 模型和参数

在监督学习里，模型就是从自变量x_i预测从因变量y_i的数学结构。一个常见的模型是线性模型，在线性模型里
<img src="https://latex.codecogs.com/gif.latex?y_i=\sum_j&space;\theta_j&space;x_{ij}" title="y_i=\sum_j \theta_j x_{ij}" />。预测的变量只是输入特征的线性组合。
预测的变量在不同任务（分类和回归）里有不同的解释。 举例来说， 我们可以通过sigmoid函数将它变换为正类的概率。我们也可以将他直接解释为输出值。

模型里的参数，我们需要从数据里去学习。 在一个线性回归问题，未知的参数就是就是 theta. 在更一般的模型里，我们还是用 theta 来表示参数。

## 目标函数：训练损失+回归

明智的选择y，我们可以完成很多不同的任务，比如回归，分类或者排名。
训练一个模型就是寻找最佳参数theta，最佳的参数应该是最符合数据和标签的参数。
为了训练模型，我们需要定义我们的目标函数来衡量我们模型和数据符合的多么好。

目标函数一个明显特征就是，他应该有两部分：训练损失和正则化项： obj(theta)= L(theta)+Omega(theta)
其中L就是训练的损失函数，而Omega就是正则化项。损失函数可以用来衡量我们的模型预言训练数据能力。
通常，L一个常用的选择是均方差（MSE），写作

<img src="https://latex.codecogs.com/gif.latex?L(\theta)=\sum_i&space;(y_i-y_i^\prime&space;)^2" title="L(\theta)=\sum_i (y_i-y_i^\prime )^2" />

另外一个通常的选择是logistic损失，通常用于logistic回归

<img src="https://latex.codecogs.com/gif.latex?L(\theta)=\sum_i[y_i\ln(1&plus;e^-y_i^\prime))&plus;(1-y_i)\ln&space;(1&plus;e^{y^\prime})]" title="L(\theta)=\sum_i[y_i\ln(1+e^-y_i^\prime))+(1-y_i)\ln (1+e^{y^\prime})]" />

人们经常忘掉加上正则化项。正则化项可以控制模型的复杂度，这可以帮助我们避免过拟合。
这看起来有点抽象，所以我们考虑下面图片里的模型。要求你拟合一个阶梯函数。
三种的哪一个答案你认为是最好的。

![](XGBoost/step_fit.png)

正确的模型是红色模型。
请思考在视觉上这是不是一个合理的拟合？
一般性的原来是我们想要一个简单而且有预言力的模型。
在机器学习领域里，两者之间的取舍也叫做偏差-方差取舍。

## 为什么引入一般原理

## 决策树集成 （基于集成的决策树，但是这个翻译太长了没有更好的翻译了）

我们已经介绍了监督学习的基本元素。现在我们转到树上。
我们首先学习XGBoost使用的模型：决策树集成。
树集成模型分类或回归树的集合组成。举一个CART的简单例子：我们采用决策树来确定某个人时候会喜欢一款电脑游戏X。

![](XGBoost/cart.png)

我们将一个家庭里的成员划分到不同的叶节点，并且给每个叶节点赋值。
一个CART和决策树有一点不同。CART的每一个叶节点只包含一个决策数值。
在CART里，一个实数分数会赋予每一个叶节点。
这让我们用CART做比分类更多的事情。
在下面部分读者将会看到，这也使得我们原则上可以将问题用统一的方式来优化。

通常，一棵树在实践中还不够强。在集成学习方法，我们是多棵树一起做预测。
![](XGBoost/twocart.png)
举一个例子，我们两棵树的树继承。两棵树的分数之和为最终用来做决定的分数。我们可以发现，两棵树起到了互相补充的作用。数学上可以把我们的模型表示为

<img src="https://latex.codecogs.com/gif.latex?y_i^\prime=\sum_{k=1}^K&space;f_k(x_i),&space;f_k&space;\in&space;F" title="y_i^\prime=\sum_{k=1}^K f_k(x_i), f_k \in F" />

这里K是树的数量，f是函数（定义域是泛型空间F），F是所有可能的CART。（注：当CART与函数f一一对应，所有分叉方法和叶节点数值确定后，CART和f也就唯一确定了）我们的目标函数是

<img src="https://latex.codecogs.com/gif.latex?obj(\theta)=\sum_i^n&space;l(y_i,y_i^\rime)&space;&plus;&space;\sum_{k=1}^K&space;\Omega(f_k)" title="obj(\theta)=\sum_i^n l(y_i,y_i^\rime) + \sum_{k=1}^K \Omega(f_k)" />

现在我们有一个棘手的问题：在随机森林的模型是什么？答案是：就是树集成啊。
所以随机森林和提升书其实是一种模型。区别在于我们怎么训练他们。
这就意味着，如果我们写下一段程序，可以从树集成得到预测值，那么这段程序也同样适用于随机森林。

# 树提升

现在我们已经介绍了模型，现在我们来学习如何训练。答案就是（对于所有的监督学习都是）定义一个目标函数并且优化。

我们把目标函数定义下面的样子

<img src="https://latex.codecogs.com/gif.latex?obj(\theta)=\sum_i^n&space;l(y_i,y_i^\rime)&space;&plus;&space;\sum_{k=1}^K&space;\Omega(f_k)" title="obj(\theta)=\sum_i^n l(y_i,y_i^\rime) + \sum_{k=1}^K \Omega(f_k)" />

## 可加性训练

我们想要问的第一个问题：树的参数是什么？我们可以发现，我们想要学习的的是函数f_i（第i课树所代表的函数），每一个函数都包含了树的结构和树的叶节点值。
学习树的结构远远要比传统的优化问题要难，不是简单的求出梯度那么简单。
同时学习树集成所有的树是个很棘手的问题。
所以，我们使用了可加性的策略。
首先固定我们已经学习到的，然后每次添加一棵树。
我们可以把第t步骤的预测值写为

<img src="https://latex.codecogs.com/gif.latex?y^{\prime(0)}_i&space;=&space;0\\&space;y^{\prime(1)}_i&space;=&space;f_1(x_i)\\&space;y^{\prime(2)}_i&space;=&space;f_1(x_i)&space;&plus;&space;f_2(x_i)\\&space;...&space;y^{\prime(t)}_i&space;=&space;y^{\prime(t-1)}_i&space;&plus;&space;f_t(x_i)\\" title="y^{\prime(0)}_i = 0\\ y^{\prime(1)}_i = f_1(x_i)\\ y^{\prime(2)}_i = f_1(x_i) + f_2(x_i)\\ ... y^{\prime(t)}_i = y^{\prime(t-1)}_i + f_t(x_i)\\" />

我们还是要问，在每一步我们想要添加什么样子的树。
一个自然的事情就是，在每一步添加的树能够优化我们的目标

![](XGBoost/f5.png)

假设我们正在使用均方差（MSE）作为我们的损失函数，我们目标变为

![](XGBoost/f6.png)

均方差的形式非常友好，目标函数的第一项是一个二次型！
其他我们感兴趣的损失函数，通常没有这么好的形式。
在更一般的情形，我们对损失函数机型泰勒展开，近似到第二阶：

![](XGBoost/f7.png)

这里 g_i和h_i定义为

![](XGBoost/f8.png)

移除所有常数项后，第t步，我们的目标函数就是

![](XGBoost/f9.png)

这就是第t步要添加的树的优化目标。这个优化目标一个重要的优势就是目标函数只依赖于g_i和h_i。这就是为什么XGBoost可以自定义损失函数。我们可以优化每一个损失函数，包括logistic回归或者对排序，只需要输入相应的g_i和h_i就可以了。

#模型复杂度

我么已经介绍了训练步骤，但是稍等，还有一件重要的事情，就是我们的正则化项。
（早说了，我们经常忘掉他们）
我们需要定义树的复杂度Omega(f)。
为了完成这个目的，我们把f(x)定义为

![](XGBoost/f10.png)

这里，w是叶节点的数值。q是从数据点到叶节点的映射(由树的结构确定)，T叶节点的数量。在XGBoost，我们定义模型复杂度为

![](XGBoost/f11.png)

当然，我们有其他的方式定义复杂度。但是上面的做法实践上表现不错。
很多基于树的软件包，对正则化的处理不够信息，甚至简单的忽视掉了。
这是因为传统基于树的教程仅仅强调提不纯度，而复杂度的控制只是留作读者遐想。
我们这里正式的定义树的复杂度，这样我们就会有更明确具体的认识。

# 结构分数

我们到了推导的非常魔幻的部分。我们重新写下树模型，我们写下第t颗树的目标函数

![](XGBoost/f12.png)

这里 I_j={i|q(x_i)=j} 是第j个叶子上所有的数据点。
注意，在第二行，第一项，我们改变求和下标。因为一个叶节点上的数值都是相等的。

我们定义 G_j=sum_(i in I_j) g_i 和 H_j = sum_{i in I_j} h_i。
（注：G_j是第j个叶子上所有数据的数值对损失函数的导数之和，H_j则是二次导数之和）
我们的目标函数现在是：

![](XGBoost/f13.png)

在上面表达式中，w_j的






















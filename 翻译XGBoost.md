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

## 决策树集成

我们已经介绍了监督学习的基本元素。现在我们转到树上。
我们首先学习XGBoost使用的模型：决策树集成。
书集成模型包含了一套分类和回归。








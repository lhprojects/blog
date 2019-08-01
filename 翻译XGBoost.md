# 翻译 XGBoost

[Introduction to Boosted Trees](https://xgboost.readthedocs.io/en/latest/tutorials/model.html)

（非技术部分的翻译并未忠实原文）

XGBoost表示Extreme Gradient Boosting，
这里术语`Gradient Boosting` 起源于Friedman的论文`Greedy Function Approximation: A Gradient Boosting Machine`. 
这是一篇关于gradient boosted tree教程，大部分内容都是基于Tianqi Chen的幻灯片，他是XGBoost原始作者。

gradient boosted tree已经存在一段时间了，已经存在这个话题大量的话题。
在这这篇教程里，我们介绍了监督学习的基本原理，并且尽量把所有相关内容都包含进来。
我们这样解释会更加清晰，更加正式，并且简洁阐述清XGBoost的模型。

# 监督学习的基本原理
XGBoost是用来解决监督学习问题的。在监督学习里，我们使用训练样本（有很多特征）x_i来预测我们目标变量y_i。
在我们学习树是什么之前，我们来看看监督学习的基本原理

# 模型和参数

在


---
title: "使用 ChatGPT 分割合并文件有感"
date: 2023-04-29 04:15:00 +0800
timezone: Asia/Shanghai
categories:
  - Tools
tags:
  - ChatGPT
  - AI
  - Thoughts
---

我有一些数据，想保存在未来十年看起来不会倒闭的并且我有权限访问的公共存储上。我自然就看上了微软家的网盘——GitHub。然而，微软家的网盘只支持小于50MB的文件。因为是当作archive存储用，我当然可以接受将文件分割成小于50MB的小文件，然后分别上传。但是微软家的网盘速度也不快，所以我最好还要压缩一下。于是我把需求写到chatgpt里让它帮我写一下代码。于是，一个巨大的txt文件，被我分割然后压缩。生成的文件如下：大概是data.txt，data.txt.partNN，data.txt.partNN.zip。然后将.zip文件上传到网盘上。
我还让chatgpt生成了一个程序，来解压缩和合并文件。但是很明显，生成的程序把原来的zip文件给删除了，我不想删除，于是我把删除语句注释掉了，看起来非常无害。但是合并的txt总有问题，我一共折腾了几个小时！最后发现原因是，合并时候脚本会合并所有名字包含part的文件，如果不删除zip文件，那么zip文件也会被合并成data.txt，就出错了。如果一开始自己写，那么我会考虑这些细节，反而比使用chatgpt更快，因为我花了很多时间debug！所以使用chatgpt这类工具，需要新的方法论，来提高效率而不是降低效率。（本文由chatgpt润色）
# Reflection on Using ChatGPT to Split and Merge Files
I have some data that I want to store on a public storage platform that seems unlikely to go bankrupt in the next decade and to which I have access. Naturally, I set my sights on Microsoft's cloud storage solution - GitHub. However, Microsoft's cloud storage only supports files smaller than 50MB. Since I am using it as an archive, I am willing to split the files into smaller ones, each less than 50MB, and upload them separately. But the upload speed on Microsoft's cloud storage is not fast, so I'd better compress the files as well. So, I asked ChatGPT to help me write some code for this task. As a result, a huge txt file was split and compressed by me. The generated files look like this: data.txt, data.txt.partNN, data.txt.partNN.zip. Then, I uploaded the .zip files to the cloud storage.
I also asked ChatGPT to create a program to decompress and merge the files. However, it was apparent that the generated program deleted the original zip files, which I didn't want to happen. So, I commented out the delete statement, which seemed harmless. But the merged txt files always had issues, and I struggled with it for several hours! Eventually, I realized that the problem was that the script would merge all files named "Part" during the merge process. If the zip files were not deleted, they would also be merged into data.txt, resulting in errors. If I had written the code myself from the beginning, I would have considered these details, which would have been faster than using ChatGPT because I spent so much time debugging! Therefore, using tools like ChatGPT requires new methodologies to improve efficiency rather than reducing it. (This text has been polished by ChatGPT)
(Translated from Chinese by ChatGPT)


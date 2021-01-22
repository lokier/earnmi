
##预测分析处理

![](imges/预测模型分析过程.jpg)

以上图解说明了如何从一个Bar一步一步分析到最终成为一个PredictData的，总得来说分以下几个步骤：
+   通过CollectorHander生成CollectData对象
+   对于finished的CollectData可以生成x,y特征做训练集合生成模型文件
+   对于unfinished的CollectData可以生成PredictData


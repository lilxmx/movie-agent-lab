"""A/B 测试分流，迁移自旧 ABTest.java。

注意：旧实现用 Java String.hashCode()，Python 无法复现且不必复现。
此处改用稳定的 int(userId) % N 分桶，逻辑等价且确定性更强。
"""
_MODELS = ["emb", "NeuralCF", "DeepCrossing", "WideAndDeep"]
_SPLIT = 3


def model_by_user_id(user_id: int) -> str:
    bucket = user_id % _SPLIT
    # bucket: 0->emb, 1->NeuralCF, 2->DeepCrossing
    return _MODELS[bucket]

from __future__ import annotations

from typing import List

try:
    from langchain.schema import Document
except ImportError:
    from langchain_core.documents import Document

from app.vector_store import vector_store
from app.documents import split_text


SAMPLE_REGULATIONS = [
    """中华人民共和国水法（摘要）
第一章 总则
第一条 为了合理开发、利用、节约和保护水资源，防治水害，实现水资源的可持续利用，适应国民经济和社会发展的需要，制定本法。

第二十条 开发、利用水资源，应当坚持兴利与除害相结合，兼顾上下游、左右岸和有关地区之间的利益，充分发挥水资源的综合效益，并服从防洪的总体安排。

第二十八条 任何单位和个人引水、截（蓄）水、排水，不得损害公共利益和他人的合法权益。

第四十八条 直接从江河、湖泊或者地下取用水资源的单位和个人，应当按照国家取水许可制度和水资源有偿使用制度的规定，向水行政主管部门或者流域管理机构申请领取取水许可证，并缴纳水资源费，取得取水权。
""",
    """取水许可和水资源费征收管理条例
第二条 本条例所称取水，是指利用取水工程或者设施直接从江河、湖泊或者地下取用水资源。

第三条 县级以上人民政府水行政主管部门按照分级管理权限，负责取水许可制度的组织实施和监督管理。

第二十条 有下列情形之一的，审批机关不予批准，并在作出不批准的决定时，书面告知申请人不批准的理由和依据：
（一）在地下水禁采区取用地下水的；
（二）在取水许可总量已经达到取水许可控制总量的地区增加取水量的；
（三）可能对水功能区水域使用功能造成重大损害的；
（四）取水、退水对水生态环境造成严重影响的；
（五）可能对第三人或者社会公共利益产生重大损害的。
""",
    """河道管理条例
第二十四条 在河道管理范围内，禁止修建围堤、阻水渠道、阻水道路；种植高杆农作物、芦苇、杞柳、荻柴和树木（堤防防护林除外）；设置拦河渔具；弃置矿渣、石渣、煤灰、泥土、垃圾等。
""",
    """取水许可申请材料要求
申请取水许可应当提交下列材料：
（一）取水许可申请书；
（二）与第三者利害关系的相关说明；
（三）属于备案项目的，提供有关备案材料；
（四）水资源论证报告书或水资源论证报告表及其审查意见。
""",
    """取水用途分类
取水许可申请书中必须包含以下必填信息：
1. 申请人基本信息：姓名、身份证号
2. 取水地点：详细地理位置
3. 取水用途：生活用水、工业用水、农业用水等
4. 取水期限：起止时间
5. 取水来源：河流、湖泊、地下水等
""",
]


def init_sample_knowledge() -> None:
    """初始化示例知识库"""
    print("加载示例法规文档...")
    
    try:
        existing_count = vector_store._collection.count()
        if existing_count > 0:
            print(f"知识库已存在 {existing_count} 条文档，跳过初始化")
            return
    except Exception as e:
        print(f"检查知识库失败: {e}")
    
    documents: List[Document] = []
    for i, text in enumerate(SAMPLE_REGULATIONS, 1):
        chunks = split_text(text)
        for j, chunk in enumerate(chunks, 1):
            doc = Document(
                page_content=chunk,
                metadata={
                    "source": f"法规文档_{i}",
                    "chunk": j,
                    "type": "regulation",
                }
            )
            documents.append(doc)
    
    try:
        vector_store.add_documents(documents)
        print(f"已添加 {len(documents)} 条文档到知识库")
    except Exception as e:
        print(f"添加文档失败: {e}")

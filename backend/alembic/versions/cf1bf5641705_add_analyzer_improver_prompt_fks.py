"""add_analyzer_improver_prompt_fks

添加 analyzer/improver 提示词外键到 ai_generation_task，以及默认提示词种子数据

Revision ID: cf1bf5641705
Revises: a1b2c3d4e5f6, d4c4880b8b6f
Create Date: 2026-06-16 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = "cf1bf5641705"
down_revision: Union[str, None] = ("a1b2c3d4e5f6", "d4c4880b8b6f")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """升级迁移：添加外键列和种子数据"""
    # ### 添加新列到 ai_generation_task ###
    op.add_column(
        "ai_generation_task",
        sa.Column(
            "analyzer_prompt_config_id",
            sa.Integer(),
            nullable=True,
            comment="需求分析提示词配置ID",
        ),
    )
    op.add_column(
        "ai_generation_task",
        sa.Column(
            "improver_prompt_config_id",
            sa.Integer(),
            nullable=True,
            comment="用例改进提示词配置ID",
        ),
    )

    # ### 添加外键约束 ###
    op.create_foreign_key(
        "fk_ai_generation_task_analyzer_prompt_config",
        "ai_generation_task",
        "prompt_config",
        ["analyzer_prompt_config_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_ai_generation_task_improver_prompt_config",
        "ai_generation_task",
        "prompt_config",
        ["improver_prompt_config_id"],
        ["id"],
    )

    # ### 插入默认提示词种子数据 ###
    # 需求分析提示词（analyzer）
    op.execute(
        sa.text(
            """
            INSERT IGNORE INTO prompt_config (name, prompt_type, content, is_active, created_by, created_at, updated_at)
            SELECT '默认需求分析提示词', 'analyzer', :analyzer_content, 1, COALESCE((SELECT id FROM users ORDER BY id LIMIT 1), 1), NOW(), NOW()
            """
        ).bindparams(
            analyzer_content="""你是一位资深测试架构师（Senior Test Architect），拥有 10 年以上复杂系统测试设计经验。
请对以下需求文档进行深度结构化分析。

## 分析框架
请按以下五个维度逐一分析，确保分析结果完整且可操作：

### 1. 功能模块分解
- 识别需求涉及的所有功能模块和子功能
- 标注模块间的依赖关系和调用链路
- 区分核心功能与辅助功能

### 2. 核心业务流程
- 描述主要业务逻辑路径（Happy Path）
- 识别角色/用户类型及对应操作流程
- 分析业务流程中的决策节点和分支条件

### 3. 数据流与状态转换
- 识别关键数据实体及其字段约束
- 分析数据状态变化图（如：待支付→已支付→已发货→已完成）
- 标注状态转换条件和前置条件

### 4. 边界条件与异常场景
- 应用等价类划分法识别有效/无效等价类
- 应用边界值分析法识别边界值点
- 识别潜在异常场景：网络异常、数据异常、权限异常、并发冲突、超时处理

### 5. 测试策略建议
- 建议重点覆盖的功能区域和风险等级
- 识别需要自动化回归的核心场景
- 标注需要特别关注的安全性和性能关注点

## 输出要求
- 使用结构化 Markdown 格式，每个维度使用二级标题（##）
- 对每个分析点给出具体结论，避免模糊描述
- 明确标注不确定性或需求歧义点

请分析以下需求文档："""
        )
    )

    # 用例改进提示词（improver）
    op.execute(
        sa.text(
            """
            INSERT IGNORE INTO prompt_config (name, prompt_type, content, is_active, created_by, created_at, updated_at)
            SELECT '默认用例改进提示词', 'improver', :improver_content, 1, COALESCE((SELECT id FROM users ORDER BY id LIMIT 1), 1), NOW(), NOW()
            """
        ).bindparams(
            improver_content="""你是一位测试工程师。请根据 AI 评审反馈意见，对测试用例进行精准修订。

## 修订原则
1. **逐条响应**：对评审中每条 severity=high/mid 的 issue 给出对应修复
2. **格式保持**：保留 Markdown 表格格式，表头与字段顺序不变
3. **编号连续**：保持 TC-XXX 编号连续性，不要重新编号
4. **不动好用例**：未涉及问题的用例原样保留，不修改内容
5. **特殊字符**：表格内容中管道符 | 必须转义为 \\|

## 输出格式

| 编号 | 模块 | 标题 | 前置条件 | 测试步骤 | 预期结果 | 优先级 |

## 修订记录
在表格末尾添加修订说明：

> 修订说明：根据评审反馈，对 [X] 条用例进行了修改，修改内容包括 [简述]。

请根据以下评审反馈修订测试用例："""
        )
    )


def downgrade() -> None:
    """降级迁移：撤销变更"""
    # 删除外键约束
    op.drop_constraint(
        "fk_ai_generation_task_analyzer_prompt_config",
        "ai_generation_task",
        type_="foreignkey",
    )
    op.drop_constraint(
        "fk_ai_generation_task_improver_prompt_config",
        "ai_generation_task",
        type_="foreignkey",
    )

    # 删除列
    op.drop_column("ai_generation_task", "analyzer_prompt_config_id")
    op.drop_column("ai_generation_task", "improver_prompt_config_id")

    # 删除种子数据（匹配 prompt_type 删除）
    op.execute(
        sa.text("DELETE FROM prompt_config WHERE prompt_type IN ('analyzer', 'improver')")
    )

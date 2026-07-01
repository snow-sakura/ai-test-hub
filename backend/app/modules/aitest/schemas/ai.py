"""
AI 测试 Pydantic 模型

定义 AI 用例生成、评测、评审等功能的请求/响应模型。
保留 AI 测试相关 schemas，模型/提示词配置相关的 schemas 移至 config_center 模块。
"""

from datetime import datetime

from pydantic import BaseModel, Field, model_validator


# ======================================================================
# AI 用例生成
# ======================================================================

class AIGenerationRequest(BaseModel):
    """AI 用例生成请求体"""
    requirement_text: str = Field(..., min_length=1, description='需求描述文本')
    project_id: int | None = Field(None, description='关联项目ID')
    writer_model_config_id: int | None = Field(None, description='编写模型配置ID')
    writer_prompt_config_id: int | None = Field(None, description='编写提示词配置ID')
    reviewer_model_config_id: int | None = Field(None, description='评审模型配置ID（为空则使用编写模型）')
    reviewer_prompt_config_id: int | None = Field(None, description='评审提示词配置ID')
    analyzer_prompt_config_id: int | None = Field(None, description='需求分析提示词配置ID')
    improver_prompt_config_id: int | None = Field(None, description='用例改进提示词配置ID')
    output_mode: str = Field('stream', description='输出模式（stream/complete）')
    enable_auto_review: bool = Field(True, description='是否启用自动评审')
    pipeline_type: str = Field(
        'traditional',
        description='生成管线类型（traditional/langgraph/autogen）',
    )
    # 保留 use_langgraph 用于旧版前端兼容
    use_langgraph: bool | None = Field(None, description='（已废弃）是否使用 LangGraph DAG 管线')
    # 继续生成相关参数
    continue_from_stage: str | None = Field(None, description='从哪个阶段继续生成（analyze/writing/review/revise）')
    continue_task_id: str | None = Field(None, description='继续生成的任务ID')

    # 向后兼容：将旧版 use_langgraph 映射到 pipeline_type
    @model_validator(mode="before")
    @classmethod
    def normalize_pipeline_type(cls, data: dict) -> dict:
        if isinstance(data, dict):
            # 旧版前端发 use_langgraph: true → 映射为 langgraph（仅当 pipeline_type 未设置时）
            if 'pipeline_type' not in data and 'use_langgraph' in data and data['use_langgraph']:
                data['pipeline_type'] = 'langgraph'
        return data


class AIGenerationResponse(BaseModel):
    """AI 用例生成响应体"""
    task_id: str = Field(..., description='任务ID')
    status: str = Field(..., description='任务状态')


class AIGenerationTaskSummary(BaseModel):
    """AI 生成任务列表项"""
    id: int = Field(..., description='数据库主键ID')
    task_id: str = Field(..., description='任务唯一标识')
    title: str = Field(..., description='任务标题')
    status: str = Field(..., description='任务状态')
    progress: int = Field(0, description='进度百分比')
    output_mode: str = Field('stream', description='输出模式')
    project_id: int | None = Field(None, description='关联项目ID')
    created_by: int = Field(..., description='创建者ID')
    saved_to_library: bool = Field(False, description='是否已保存到用例库')
    created_at: datetime = Field(..., description='创建时间')
    completed_at: datetime | None = Field(None, description='完成时间')

    model_config = {"from_attributes": True}


class GeneratedTestCaseItem(BaseModel):
    """生成的测试用例项"""
    id: int | None = Field(None, description='ID')
    case_id: str = Field(..., description='用例编号')
    title: str = Field(..., description='用例标题')
    module: str | None = Field(None, description='所属模块')
    priority: str = Field('P2', description='优先级（P0/P1/P2/P3）')
    precondition: str | None = Field(None, description='前置条件')
    test_steps: str | None = Field(None, description='测试步骤')
    expected_result: str | None = Field(None, description='预期结果')
    status: str = Field('generated', description='用例状态')

    model_config = {"from_attributes": True}


class AITaskDetailResponse(BaseModel):
    """AI 任务详情响应体"""
    id: int
    task_id: str
    title: str
    status: str
    progress: int
    requirement_text: str
    output_mode: str
    project_id: int | None = None
    writer_model_config_id: int | None = None
    reviewer_model_config_id: int | None = None
    writer_prompt_config_id: int | None = None
    reviewer_prompt_config_id: int | None = None
    analyzer_prompt_config_id: int | None = None
    improver_prompt_config_id: int | None = None
    created_by: int
    generated_content: dict | None = None
    review_feedback: str | None = None
    final_content: dict | None = None
    error_message: str | None = None
    saved_to_library: bool = Field(False, description='是否已保存到用例库')
    created_at: datetime | None = None
    completed_at: datetime | None = None
    # 关联的用例列表
    test_cases: list[GeneratedTestCaseItem] = Field(default_factory=list)

    model_config = {"from_attributes": True}


# ======================================================================
# AI 模型/提示词配置概要（下拉选择，保留在 AI 测试模块以便前端使用）
# ======================================================================

class AIModelConfigSummary(BaseModel):
    """AI 模型配置概要（用于下拉选择）"""
    id: int
    name: str
    model_type: str
    role: str
    model_name: str
    is_active: bool

    model_config = {"from_attributes": True}


class PromptConfigSummary(BaseModel):
    """提示词配置概要（用于下拉选择）"""
    id: int
    name: str
    prompt_type: str
    is_active: bool

    model_config = {"from_attributes": True}


# ======================================================================
# AI 评测
# ======================================================================

class EvaluationIssue(BaseModel):
    """评测问题项"""
    severity: str = Field(..., description='严重等级（high/mid/low）')
    title: str = Field(..., description='问题标题')
    description: str = Field('', description='问题描述')
    fix_suggestion: str = Field('', description='修复建议')
    related_cases: str = Field('', description='相关用例编号')


class AIReviseRequest(BaseModel):
    """AI 任务修订请求体"""
    pipeline_type: str = Field(
        'traditional',
        description='生成管线类型（traditional/langgraph/autogen）',
    )


class AIEvaluationRequest(BaseModel):
    """AI 评测请求体"""
    test_cases: list[str] = Field(..., min_length=1, description='待评测的用例列表（文本形式）')
    model_config_id: int = Field(..., description='评测模型配置ID')
    prompt_config_id: int = Field(..., description='评测提示词配置ID')


class AIEvaluationResponse(BaseModel):
    """AI 评测响应体"""
    overall_score: float = Field(0, description='综合评分（0-100）')
    issues: list[EvaluationIssue] = Field(default_factory=list, description='问题列表')
    improvements: list[str] = Field(default_factory=list, description='改进建议')
    detail: str = Field('', description='AI 原始评测文本')


# ======================================================================
# AI 评审
# ======================================================================

class AIReviewRequest(BaseModel):
    """AI 评审请求体"""
    task_id: str = Field(..., description='任务ID')
    test_cases: str = Field(..., description='待评审的用例内容（文本格式）')


class AIReviewResponse(BaseModel):
    """AI 评审响应体"""
    task_id: str = Field(..., description='任务ID')
    feedback: str = Field(..., description='评审反馈内容')
    status: str = Field(..., description='评审状态')


# ======================================================================
# AI 测试报告
# ======================================================================

class AIReportSummary(BaseModel):
    """AI 测试报告列表项"""
    id: int = Field(..., description='任务数据库ID')
    task_id: str = Field(..., description='任务唯一标识')
    title: str = Field(..., description='报告标题（任务标题）')
    project_name: str = Field('', description='关联项目名称')
    status: str = Field(..., description='任务状态')
    total_cases: int = Field(0, description='总用例数')
    passed: int = Field(0, description='通过数')
    failed: int = Field(0, description='失败数')
    blocked: int = Field(0, description='阻塞数')
    pass_rate: float = Field(0.0, description='通过率')
    created_at: str = Field('', description='创建时间')

    model_config = {"from_attributes": True}


class FailedCaseItem(BaseModel):
    """失败用例详情项"""
    case_id: str = Field(..., description='用例编号')
    title: str = Field(..., description='用例标题')
    module: str = Field('', description='所属模块')
    priority: str = Field('P2', description='优先级')
    reason: str = Field('', description='失败原因（当前状态描述）')
    status: str = Field('', description='用例状态')


class ModuleStatItem(BaseModel):
    """模块分布统计项"""
    module: str = Field(..., description='模块名称')
    total: int = Field(0, description='该模块总用例数')
    passed: int = Field(0, description='通过数')
    failed: int = Field(0, description='失败数')
    pass_rate: float = Field(0.0, description='通过率')


class AIReportStats(BaseModel):
    """AI 测试报告统计数据"""
    total_cases: int = Field(0, description='总用例数')
    passed: int = Field(0, description='通过数')
    failed: int = Field(0, description='失败数')
    blocked: int = Field(0, description='阻塞数')
    pass_rate: float = Field(0.0, description='通过率')
    module_stats: list[ModuleStatItem] = Field(default_factory=list, description='模块分布统计')
    failed_cases: list[FailedCaseItem] = Field(default_factory=list, description='失败用例列表')


class AIReportDetail(BaseModel):
    """AI 测试报告详情"""
    summary: AIReportSummary = Field(..., description='报告概要')
    stats: AIReportStats = Field(..., description='统计数据')
    cases: list[GeneratedTestCaseItem] = Field(default_factory=list, description='全部用例明细')


# ======================================================================
# AI 智能模式配置
# ======================================================================

class AISettingsResponse(BaseModel):
    """AI 智能模式配置响应"""
    # 基础配置
    ai_mode_enabled: bool = Field(True, description='启用AI模式')
    auto_trigger_on_requirement_change: bool = Field(False, description='需求变更自动触发')
    auto_generate_report: bool = Field(False, description='自动生成报告')
    auto_retest_on_failure: bool = Field(False, description='失败自动重测')
    notification_config: dict | None = Field(None, description='通知配置(JSON)')

    # 模型配置
    provider: str = Field('', description='AI提供商')
    api_key: str = Field('', description='API Key（脱敏）')
    model_name: str = Field('', description='模型名称')
    temperature: float = Field(0.7, description='温度参数')
    context_window: int = Field(128000, description='上下文窗口大小')

    # 高级配置
    max_input_tokens: int = Field(128000, description='最大输入Token')
    max_output_tokens: int = Field(4096, description='最大输出Token')
    retry_count: int = Field(3, description='重试次数')
    timeout_seconds: int = Field(120, description='超时时间(秒)')
    concurrency: int = Field(1, description='并发数')
    rate_limit_rpm: int = Field(60, description='速率限制(RPM)')
    custom_prompt_template: str | None = Field(None, description='自定义Prompt模板')

    id: int = Field(0, description='主键ID')
    created_by: int = Field(0, description='创建者ID')
    created_at: str = Field('', description='创建时间')
    updated_at: str = Field('', description='更新时间')

    model_config = {"from_attributes": True}


class AISettingsUpdate(BaseModel):
    """更新 AI 智能模式配置请求"""
    # 基础配置
    ai_mode_enabled: bool | None = Field(None, description='启用AI模式')
    auto_trigger_on_requirement_change: bool | None = Field(None, description='需求变更自动触发')
    auto_generate_report: bool | None = Field(None, description='自动生成报告')
    auto_retest_on_failure: bool | None = Field(None, description='失败自动重测')
    notification_config: dict | None = Field(None, description='通知配置(JSON)')

    # 模型配置
    provider: str | None = Field(None, description='AI提供商')
    api_key: str | None = Field(None, description='API Key')
    model_name: str | None = Field(None, description='模型名称')
    temperature: float | None = Field(None, description='温度参数')
    context_window: int | None = Field(None, description='上下文窗口大小')

    # 高级配置
    max_input_tokens: int | None = Field(None, description='最大输入Token')
    max_output_tokens: int | None = Field(None, description='最大输出Token')
    retry_count: int | None = Field(None, description='重试次数')
    timeout_seconds: int | None = Field(None, description='超时时间(秒)')
    concurrency: int | None = Field(None, description='并发数')
    rate_limit_rpm: int | None = Field(None, description='速率限制(RPM)')
    custom_prompt_template: str | None = Field(None, description='自定义Prompt模板')

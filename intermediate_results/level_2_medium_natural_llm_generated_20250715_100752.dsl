# LLM Generated DSL Code
# Source: sop_test_cases/level_2_medium_natural.txt
# Generated at: 2025-07-15T10:07:52.572086
# Provider: openai
# Model: deepseek-chat-0324

@var customer_type = ""
@var severity_level = ""
@var satisfaction_score = 0

@task receive_complaint 接收与评估投诉
    使用CRM系统创建新投诉工单
    @tool crm_system_create 创建投诉工单
    记录客户信息、联系方式和投诉详情
    设置投诉严重等级：{{severity_level}}
    查询客户类型：{{customer_type}}
    @if severity_level == "高" OR customer_type == "VIP客户"
        @next escalate_complaint
    @else
        @next regular_processing

@task regular_processing 常规处理
    分配给常规处理团队
    联系客户了解问题细节
    进行内部调查并制定解决方案
    实施解决方案
    @next customer_followup

@task escalate_complaint 升级处理
    分配给高级支持团队
    @tool notification_service 通知相关部门
    制定紧急处理计划
    保持与客户实时沟通
    解决问题
    @next customer_followup

@task customer_followup 客户沟通与确认
    联系客户说明处理结果
    @tool satisfaction_survey 收集满意度评分
    @if satisfaction_score >= 4
        @next close_case
    @else
        @next reprocess_complaint

@task reprocess_complaint 重新处理
    重新激活工单状态
    指派给更高级别人员
    重新评估问题
    提供额外补偿方案
    实施新解决方案
    @next customer_followup

@task close_case 结案归档
    更新工单状态为"已解决"
    @tool crm_system_update 更新工单状态
    撰写结案报告
    归档所有记录
    @next END

@task END 流程结束
    投诉处理流程完成
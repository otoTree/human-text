# LLM Generated DSL Code
# Source: sop_test_cases/level_2_medium_natural.txt
# Generated at: 2025-07-15T10:08:09.144390
# Provider: openai
# Model: deepseek-chat-0324

@var complaint_severity = ""
@var customer_type = ""

@task receive_complaint 接收与评估投诉
    使用CRM系统创建新的投诉工单
    @tool crm_system_create 创建投诉工单
    记录客户信息、联系方式和投诉内容
    初步设置投诉严重等级：{{complaint_severity}}
    查询客户类型：{{customer_type}}
    @if complaint_severity == "高" OR customer_type == "VIP客户"
        @next escalate_complaint
    @else
        @next regular_processing

@task regular_processing 常规处理
    分配给常规处理团队
    主动联系客户了解问题细节
    展开内部调查并制定解决方案
    实施解决方案
    @next customer_confirmation

@task escalate_complaint 升级处理
    分配给高级支持团队或客服主管
    通知相关其他部门
    @tool notification_service 发送紧急通知
    制定紧急处理计划并调动资源
    保持与客户的实时沟通
    问题解决后
    @next customer_confirmation

@task customer_confirmation 客户沟通与确认
    联系客户说明处理过程和结果
    收集客户满意度评分
    @tool satisfaction_survey 满意度调查工具
    @if satisfaction_score >= 4
        @next close_case
    @else
        @next reprocess_complaint

@task reprocess_complaint 重新处理
    重新激活工单状态
    指派给更高级别技术人员或主管
    重新评估问题并提供补偿方案
    实施新解决方案
    @next customer_confirmation

@task close_case 结案归档
    在CRM系统中更新工单状态为"已解决"
    @tool crm_system_update 更新工单状态
    撰写详细结案报告并归档
    @next END

@task END 流程结束
    客户投诉处理流程完成
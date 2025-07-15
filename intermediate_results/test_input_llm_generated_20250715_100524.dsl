# LLM Generated DSL Code
# Source: example/test_input.txt
# Generated at: 2025-07-15T10:05:24.362547
# Provider: openai
# Model: deepseek-chat-0324

@var order_id = ""
@var payment_amount = 0
@var payment_threshold = 1000

@task check_order Check order validity
    订单号：{{order_id}}
    @if order_id == ""
        订单无效，终止流程
        @next log_result
    @else
        @next verify_payment

@task verify_payment Verify payment amount
    @tool payment_system_check 检查支付金额是否超过阈值
    @if payment_amount > payment_threshold
        Payment is acceptable
        @next thank_customer
    @else
        Payment rejected
        @next log_result

@task thank_customer Thank customer
    感谢您的购买！
    @next log_result

@task log_result Log process result
    流程结束，写入日志
    @tool system_logger 记录订单处理结果
    @next END

@task END Process complete
    订单处理流程结束
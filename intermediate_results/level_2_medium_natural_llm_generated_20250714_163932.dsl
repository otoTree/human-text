# LLM Generated DSL Code
# Source: sop_test_cases/level_2_medium_natural.txt
# Generated at: 2025-07-14T16:39:32.255301
# Provider: openai
# Model: deepseek-chat-0324

@var complaint_severity = ""
@var customer_type = ""
@var satisfaction_score = 0

@task receive_complaint Receive and evaluate complaint
    Create new complaint ticket in CRM system
    @tool crm_system_create Create complaint ticket
    Record customer info, contact details and complaint content
    Set initial severity level: {{complaint_severity}}
    Analyze complaint severity
    Query customer type: {{customer_type}}
    @if complaint_severity == "high" OR customer_type == "VIP"
        @next escalate_complaint
    @else
        @next regular_processing

@task regular_processing Regular processing
    Assign ticket to regular support team
    Contact customer for details
    Conduct internal investigation
    Develop solution and implement
    @next customer_confirmation

@task escalate_complaint Escalate complaint
    Assign ticket to senior support team
    @tool notification_service_alert Notify relevant departments
    Create emergency action plan
    Maintain real-time communication with customer
    Implement solution
    @next customer_confirmation

@task customer_confirmation Customer communication and confirmation
    Contact customer to explain solution
    Collect satisfaction score: {{satisfaction_score}}
    @tool satisfaction_survey Collect feedback
    @if satisfaction_score >= 4
        @next close_case
    @else
        @next reprocess_complaint

@task reprocess_complaint Re-process complaint
    Reactivate ticket status
    Assign to higher-level technician
    Re-evaluate problem
    Develop additional compensation if needed
    Implement new solution
    @next customer_confirmation

@task close_case Close and archive case
    Update ticket status to "Resolved" in CRM
    @tool crm_system_update Update ticket status
    Write detailed closure report
    Archive all records and communications
    @next END

@task END Process complete
    Complaint handling process completed
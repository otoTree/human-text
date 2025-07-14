# LLM Generated DSL Code
# Source: sop_test_cases/level_2_medium_natural.txt
# Generated at: 2025-07-14T16:36:49.290844
# Provider: openai
# Model: deepseek-chat-0324

@var customer_type = ""
@var severity_level = ""
@var satisfaction_score = 0

@task receive_complaint Receive and evaluate complaint
    Create new complaint ticket in CRM system
    @tool crm_system_create Create new complaint ticket
    Record customer info, contact details and complaint content
    Set initial severity level (low/medium/high)
    Analyze complaint severity
    Query customer type (regular/VIP)
    @if severity_level == "high" OR customer_type == "VIP"
        @next escalate_complaint
    @else
        @next regular_processing

@task regular_processing Regular processing
    Assign ticket to regular support team
    Contact customer for additional details
    Conduct internal investigation
    Identify root cause and develop solution
    Implement solution
    @next customer_confirmation

@task escalate_complaint Escalate complaint
    Assign ticket to senior support team
    @tool notification_service_alert Notify relevant departments
    Develop emergency action plan
    Allocate high-priority resources
    Maintain real-time communication with customer
    Implement solution
    @next customer_confirmation

@task customer_confirmation Customer communication and confirmation
    Contact customer to explain resolution
    Collect satisfaction score via survey
    @tool satisfaction_survey_tool Collect feedback
    @if satisfaction_score >= 4
        @next close_case
    @else
        @next reprocess_complaint

@task reprocess_complaint Reprocess complaint
    Reactivate ticket status
    Assign to higher-level technician/manager
    Re-evaluate entire issue
    Develop additional compensation if needed
    Implement new solution
    @next customer_confirmation

@task close_case Close and archive case
    Update ticket status to "Resolved" in CRM
    @tool crm_system_update Update ticket status
    Prepare detailed closure report
    Archive all communication records and solutions
    @next END

@task END Process complete
    Complaint handling process completed
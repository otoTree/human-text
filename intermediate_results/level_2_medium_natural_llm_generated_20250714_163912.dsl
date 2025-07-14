# LLM Generated DSL Code
# Source: sop_test_cases/level_2_medium_natural.txt
# Generated at: 2025-07-14T16:39:12.031814
# Provider: openai
# Model: deepseek-chat-0324

@var customer_type = ""
@var severity_level = ""
@var satisfaction_score = 0

@task receive_complaint Receive and evaluate complaint
    Create new complaint ticket in CRM system
    @tool crm_system_create Create complaint ticket
    Record customer info, contact details and complaint content
    Set initial severity level (low/medium/high)
    Analyze complaint severity
    Query customer type (normal/VIP)
    @if severity_level == "high" or customer_type == "VIP"
        @next escalate_complaint
    @else
        @next regular_processing

@task regular_processing Regular processing
    Assign to regular support team
    Contact customer for details
    Conduct internal investigation
    Identify root cause
    Develop solution
    Implement solution
    @next customer_communication

@task escalate_complaint Escalate complaint
    Assign to senior support team
    @tool notification_service Alert relevant departments
    Develop emergency plan
    Allocate high-priority resources
    Maintain real-time communication with customer
    Resolve issue
    @next customer_communication

@task customer_communication Customer communication and confirmation
    Contact customer to explain resolution
    Collect satisfaction feedback
    @tool satisfaction_survey Conduct satisfaction survey
    @if satisfaction_score >= 4
        @next close_case
    @else
        @next reprocess_complaint

@task reprocess_complaint Reprocess complaint
    Reactivate ticket status
    Assign to higher-level technician
    Re-evaluate entire issue
    Develop additional compensation if needed
    Implement new solution
    @next customer_communication

@task close_case Close and archive case
    Update ticket status to "Resolved" in CRM
    @tool crm_system_update Update ticket status
    Prepare detailed closure report
    Archive all communication records and solutions
    @next END

@task END Process complete
    Complaint handling process completed
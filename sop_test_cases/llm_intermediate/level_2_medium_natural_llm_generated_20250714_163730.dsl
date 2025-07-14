# LLM Generated DSL Code
# Source: sop_test_cases/level_2_medium_natural.txt
# Generated at: 2025-07-14T16:37:30.423853
# Provider: openai
# Model: deepseek-chat-0324

@var customer_type = ""
@var severity_level = ""
@var satisfaction_score = 0

@task receive_complaint Receive and evaluate complaint
    Create new complaint ticket in CRM system
    @tool crm_system_create Create new complaint ticket
    Record customer info, contact details, and complaint content
    Set initial severity level: {{severity_level}}
    Perform preliminary assessment
    @tool crm_system_query Check customer type: {{customer_type}}
    @if severity_level == "high" or customer_type == "VIP"
        @next escalate_complaint
    @else
        @next regular_processing

@task regular_processing Regular processing
    Assign to regular support team
    Contact customer for details
    Conduct internal investigation
    Develop solution and implement
    @next customer_communication

@task escalate_complaint Escalate complaint
    Assign to senior support team
    @tool notification_service Alert relevant departments
    Create emergency action plan
    Maintain real-time communication with customer
    Resolve issue
    @next customer_communication

@task customer_communication Customer communication and confirmation
    Contact customer to explain solution
    Collect satisfaction score: {{satisfaction_score}}
    @tool satisfaction_survey Conduct satisfaction survey
    @if satisfaction_score >= 4
        @next close_case
    @else
        @next reprocess_complaint

@task reprocess_complaint Reprocess complaint
    Reactivate ticket status
    Assign to higher-level technician
    Re-evaluate problem
    Provide additional compensation if needed
    Implement new solution
    @next customer_communication

@task close_case Close and archive case
    Update ticket status to "Resolved"
    @tool crm_system_update Update ticket status
    Write detailed case report
    Archive all records
    @next END

@task END Process complete
    Complaint handling process completed
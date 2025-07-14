# LLM Generated DSL Code
# Source: sop_test_cases/level_2_medium_natural.txt
# Generated at: 2025-07-14T16:36:30.248793
# Provider: openai
# Model: deepseek-chat-0324

@var customer_type = ""
@var severity_level = ""
@var satisfaction_score = 0

@task receive_assess_complaint Receive and assess complaint
    Create new complaint ticket in CRM system
    @tool crm_system_create Create new complaint ticket
    Record customer info, contact details and complaint content
    Set initial severity level: {{severity_level}}
    Perform preliminary assessment
    @tool crm_system_query Check customer type: {{customer_type}}
    @if severity_level == "high" or customer_type == "VIP"
        @next escalate_handling
    @else
        @next regular_handling

@task regular_handling Regular handling
    Assign to regular support team
    Contact customer for details
    Conduct internal investigation
    Develop solution and implement
    @next customer_communication

@task escalate_handling Escalate handling
    Assign to senior support team
    @tool notification_service Alert relevant departments
    Create emergency action plan
    Maintain real-time communication with customer
    Implement solution
    @next customer_communication

@task customer_communication Customer communication and confirmation
    Explain resolution process to customer
    Collect satisfaction score: {{satisfaction_score}}
    @tool satisfaction_survey Collect customer feedback
    @if satisfaction_score >= 4
        @next close_case
    @else
        @next reprocess_complaint

@task reprocess_complaint Re-process complaint
    Reactivate ticket status
    Assign to higher-level technician/supervisor
    Re-evaluate problem and develop new solution
    Possibly offer additional compensation
    Implement new solution
    @next customer_communication

@task close_case Close and archive case
    Update ticket status to "Resolved"
    @tool crm_system_update Update ticket status
    Prepare detailed closure report
    Archive all records and feedback
    @next END

@task END Process complete
    Complaint handling process completed
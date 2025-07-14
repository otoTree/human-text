# LLM Generated DSL Code
# Source: sop_test_cases/level_2_medium_natural.txt
# Generated at: 2025-07-14T16:34:20.743049
# Provider: openai
# Model: deepseek-chat-0324

@var complaint_severity = ""
@var customer_type = ""

@task receive_assess_complaint Receive and assess complaint
    Create new complaint ticket in CRM system
    @tool crm_system_create Create complaint ticket
    Record customer info, contact details, complaint content
    Set initial severity level (low/medium/high)
    Analyze complaint severity
    Query customer type (regular/VIP)
    @if complaint_severity == "high" OR customer_type == "VIP"
        @next escalate_complaint
    @else
        @next regular_processing

@task regular_processing Regular processing
    Assign ticket to regular support team
    Contact customer for details
    Conduct internal investigation
    Identify root cause and develop solution
    Implement solution
    @next customer_communication

@task escalate_complaint Escalate complaint
    Assign ticket to senior support team
    @tool notification_service_alert Notify relevant departments
    Develop emergency action plan
    Allocate high-priority resources
    Maintain real-time communication with customer
    Implement solution
    @next customer_communication

@task customer_communication Customer communication and confirmation
    Contact customer to explain solution
    Collect customer satisfaction score
    @tool satisfaction_survey_collect Conduct satisfaction survey
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

@task close_case Close case and archive
    Update ticket status to "Resolved" in CRM
    @tool crm_system_update Update ticket status
    Write detailed case report
    Archive all communication records and solutions
    @next END

@task END Process complete
    Complaint handling process completed
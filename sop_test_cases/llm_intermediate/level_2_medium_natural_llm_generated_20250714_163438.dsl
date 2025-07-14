# LLM Generated DSL Code
# Source: sop_test_cases/level_2_medium_natural.txt
# Generated at: 2025-07-14T16:34:38.115557
# Provider: openai
# Model: deepseek-chat-0324

@var customer_type = ""
@var severity_level = ""
@var satisfaction_score = 0

@task receive_complaint Receive and evaluate complaint
    Create new complaint ticket in CRM system
    @tool crm_system_create Record customer info and complaint details
    Set initial severity level: {{severity_level}}
    Identify customer type: {{customer_type}}
    Perform initial assessment
    @if severity_level == "high" OR customer_type == "VIP"
        @next escalate_complaint
    @else
        @next regular_processing

@task regular_processing Regular processing
    Assign to regular support team
    Contact customer for details
    Conduct internal investigation
    Develop solution
    Implement solution
    @next customer_confirmation

@task escalate_complaint Escalate complaint
    Assign to senior support team
    @tool notification_service Alert relevant departments
    Create emergency action plan
    Allocate high-priority resources
    Maintain real-time communication
    Resolve issue
    @next customer_confirmation

@task customer_confirmation Customer communication and confirmation
    Contact customer with resolution
    Explain process and outcome
    Collect satisfaction feedback
    @tool satisfaction_survey Get customer rating
    @if satisfaction_score >= 4
        @next close_case
    @else
        @next reprocess_complaint

@task reprocess_complaint Re-process complaint
    Reactivate ticket status
    Assign to higher-level technician
    Re-evaluate entire issue
    Develop additional compensation
    Implement new solution
    @next customer_confirmation

@task close_case Close and archive case
    Update ticket status to "Resolved"
    @tool crm_system_update Finalize ticket
    Write detailed closure report
    Archive all records
    @next END

@task END Process complete
    Complaint handling process completed
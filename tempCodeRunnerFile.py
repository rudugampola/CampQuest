
output, has_availabilities = run_campsite_check(
    parks=[232447], 
    start_date=datetime(2024, 12, 11), 
    end_date=datetime(2024, 12, 14), 
    json_output=True
)

print(output)
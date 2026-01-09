def correlate(username_results, phone_data, dob_found):
    links = []
    for platform, data in username_results.items():
        if data.get("found"):
            links.append(platform)
            
    return {
        "linked_platforms": links,
        "phone_valid": phone_data.get("valid"),
        "dob_exposed": dob_found
    }
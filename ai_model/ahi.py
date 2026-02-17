def calculate_ahi(predictions, total_minutes):
    events = sum(predictions)
    hours = total_minutes / 60
    ahi = events / hours

    if ahi < 5:
        severity = "Normal"
    elif ahi < 15:
        severity = "Mild"
    elif ahi < 30:
        severity = "Moderate"
    else:
        severity = "Severe"

    return ahi, severity, events


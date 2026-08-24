"""Related operational records shown from an Attendance document."""


def get_data():
	return {
		"fieldname": "attendance",
		"transactions": [
			{
				"label": "Attendance Operations",
				"items": ["Employee Checkin", "Overtime Request"],
			}
		],
	}

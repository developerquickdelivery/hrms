frappe.ui.form.on("Goal", {
	refresh(frm) {
		frm.set_query("source_name", "custom_qd_metric_sources", (doc, cdt, cdn) => {
			const row = locals[cdt][cdn];
			return { filters: row.source_doctype === "Task" ? { status: ["!=", "Template"] } : {} };
		});
	},
	custom_qd_kpi_actual(frm) {
		if (frm.doc.custom_qd_kpi_target && flt(frm.doc.custom_qd_kpi_target) > 0) {
			const pct = (flt(frm.doc.custom_qd_kpi_actual) / flt(frm.doc.custom_qd_kpi_target)) * 100;
			if (!(frm.doc.custom_qd_metric_sources || []).length) {
				frm.set_value("progress", Math.max(0, Math.min(100, pct)));
			}
		}
	},
});

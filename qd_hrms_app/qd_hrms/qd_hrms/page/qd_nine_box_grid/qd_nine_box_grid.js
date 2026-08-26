frappe.pages["qd-nine-box-grid"].on_page_load = (wrapper) => {
	new QDNineBoxGrid(wrapper);
};

class QDNineBoxGrid {
	constructor(wrapper) {
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Executive Nine-Box Grid"),
			single_column: true,
		});
		this.rows = [];
		this.make_toolbar();
		this.$body = $(`<div class="qd-nine-box-page"></div>`).appendTo(this.page.main);
	}

	make_toolbar() {
		this.calibration = this.page.add_field({
			label: __("Calibration"),
			fieldtype: "Link",
			fieldname: "calibration",
			options: "QD Performance Calibration",
			change: () => this.load(),
			get_query: () => ({ filters: { docstatus: ["<", 2] } }),
		});
		this.search = this.page.add_field({
			label: __("Employee"),
			fieldtype: "Data",
			fieldname: "employee_search",
			change: () => this.render(),
		});
		this.risk = this.page.add_field({
			label: __("Retention Risk"),
			fieldtype: "Select",
			fieldname: "retention_risk",
			options: "\nLow\nMedium\nHigh",
			change: () => this.render(),
		});
		this.page.add_button(__("Refresh"), () => this.load(), "refresh");
		const route = frappe.get_route();
		if (route[1]) {
			this.calibration.set_value(route[1]);
		}
	}

	async load() {
		const calibration = this.calibration.get_value();
		if (!calibration) {
			this.$body.html(this.empty_state(__("Select a calibration to review talent placement.")));
			return;
		}
		this.$body.html(`<div class="qd-nine-box-loading">${__("Loading calibration…")}</div>`);
		const response = await frappe.call({
			method: "qd_hrms.performance.get_nine_box_data",
			args: { calibration },
			freeze: true,
		});
		this.data = response.message;
		this.rows = this.data?.rows || [];
		this.render();
	}

	filtered_rows() {
		const query = (this.search.get_value() || "").trim().toLowerCase();
		const risk = this.risk.get_value();
		return this.rows.filter((row) => {
			const matches_query =
				!query ||
				`${row.employee || ""} ${row.employee_name || ""}`.toLowerCase().includes(query);
			return matches_query && (!risk || row.retention_risk === risk);
		});
	}

	render() {
		if (!this.data) return;
		const rows = this.filtered_rows();
		const highPotential = rows.filter((row) => row.potential_level === "High").length;
		const futureLeaders = rows.filter((row) => row.nine_box === "Future Leader").length;
		const highRisk = rows.filter((row) => row.retention_risk === "High").length;
		const editable = this.data.docstatus === 0 && this.data.approval_status !== "Completed";
		this.$body.html(`
			<div class="qd-nine-box-summary">
				${this.metric(__("Employees"), rows.length)}
				${this.metric(__("High Potential"), highPotential)}
				${this.metric(__("Future Leaders"), futureLeaders)}
				${this.metric(__("High Retention Risk"), highRisk, highRisk ? "danger" : "")}
			</div>
			<div class="qd-nine-box-context">
				<div><b>${frappe.utils.escape_html(this.data.appraisal_cycle || "")}</b>
					${this.data.department ? ` · ${frappe.utils.escape_html(this.data.department)}` : ""}
				</div>
				<div class="text-muted">${editable
					? __("Drag an employee card to update placement. Changes are audited on the calibration document.")
					: __("This calibration is read-only.")}</div>
			</div>
			<div class="qd-nine-box-matrix">
				<div class="qd-axis-potential">${__("POTENTIAL")}</div>
				${["High", "Moderate", "Low"].map((potential) => `
					<div class="qd-axis-row">${__(potential)}</div>
					${["Low", "Moderate", "High"].map((performance) =>
						this.box(rows, performance, potential, editable)
					).join("")}
				`).join("")}
				<div></div><div class="qd-axis-column">${__("Low")}</div>
				<div class="qd-axis-column">${__("Moderate")}</div>
				<div class="qd-axis-column">${__("High")}</div>
				<div></div><div class="qd-axis-performance">${__("PERFORMANCE")}</div>
			</div>
		`);
		this.bind_events(editable);
	}

	box(rows, performance, potential, editable) {
		const labels = {
			"Low|Low": __("Underperformer"),
			"Moderate|Low": __("Effective Professional"),
			"High|Low": __("Trusted Expert"),
			"Low|Moderate": __("Inconsistent Player"),
			"Moderate|Moderate": __("Core Contributor"),
			"High|Moderate": __("High Impact Performer"),
			"Low|High": __("Potential Gem"),
			"Moderate|High": __("Emerging Talent"),
			"High|High": __("Future Leader"),
		};
		const key = `${performance}|${potential}`;
		const boxRows = rows.filter(
			(row) => row.performance_level === performance && row.potential_level === potential
		);
		const cards = boxRows.map((row) => this.card(row, editable)).join("");
		return `<div class="qd-nine-box-cell qd-box-${performance.toLowerCase()}-${potential.toLowerCase()}"
			data-performance="${performance}" data-potential="${potential}">
			<div class="qd-nine-box-cell-title">
				<span>${labels[key]}</span><span class="badge">${boxRows.length}</span>
			</div>
			<div class="qd-nine-box-cards">${cards || `<span class="text-muted">${__("No employees")}</span>`}</div>
		</div>`;
	}

	card(row, editable) {
		const risk = row.retention_risk === "High"
			? `<span class="indicator-pill red">${__("High risk")}</span>` : "";
		const critical = row.critical_role
			? `<span class="indicator-pill orange">${__("Critical")}</span>` : "";
		return `<div class="qd-talent-card" draggable="${editable ? "true" : "false"}"
			data-appraisal="${frappe.utils.escape_html(row.appraisal)}">
			<div class="qd-talent-name">${frappe.utils.escape_html(row.employee_name || row.employee)}</div>
			<div class="qd-talent-code">${frappe.utils.escape_html(row.employee || "")}</div>
			<div class="qd-talent-scores">
				<span>${__("P")}: ${Number(row.calibrated_score || 0).toFixed(2)}</span>
				<span>${__("Pot")}: ${Number(row.potential_score || 0).toFixed(2)}</span>
			</div>
			<div>${risk}${critical}</div>
		</div>`;
	}

	bind_events(editable) {
		this.$body.find(".qd-talent-card").on("click", (event) => {
			const row = this.rows.find((item) => item.appraisal === event.currentTarget.dataset.appraisal);
			if (row) this.edit_placement(row, row.performance_level, row.potential_level, editable);
		});
		if (!editable) return;
		this.$body.find(".qd-talent-card").on("dragstart", (event) => {
			event.originalEvent.dataTransfer.setData("text/plain", event.currentTarget.dataset.appraisal);
		});
		this.$body.find(".qd-nine-box-cell")
			.on("dragover", (event) => event.preventDefault())
			.on("drop", (event) => {
				event.preventDefault();
				const appraisal = event.originalEvent.dataTransfer.getData("text/plain");
				const row = this.rows.find((item) => item.appraisal === appraisal);
				if (row) {
					this.edit_placement(
						row,
						event.currentTarget.dataset.performance,
						event.currentTarget.dataset.potential,
						true
					);
				}
			});
	}

	edit_placement(row, performance, potential, editable) {
		const dialog = new frappe.ui.Dialog({
			title: row.employee_name || row.employee,
			fields: [
				{ fieldname: "performance_level", label: __("Performance"), fieldtype: "Select",
					options: "Low\nModerate\nHigh", reqd: 1, default: performance },
				{ fieldname: "potential_level", label: __("Potential"), fieldtype: "Select",
					options: "Low\nModerate\nHigh", reqd: 1, default: potential },
				{ fieldname: "retention_risk", label: __("Retention Risk"), fieldtype: "Select",
					options: "Low\nMedium\nHigh", default: row.retention_risk || "Low" },
				{ fieldname: "critical_role", label: __("Critical Role"), fieldtype: "Check",
					default: row.critical_role },
				{ fieldname: "successor_ready", label: __("Successor Ready"), fieldtype: "Check",
					default: row.successor_ready },
				{ fieldname: "development_action", label: __("Development / Succession Action"),
					fieldtype: "Small Text", default: row.development_action },
				{ fieldname: "rationale", label: __("Executive Rationale"), fieldtype: "Small Text",
					reqd: 1, default: row.rationale },
			],
			primary_action_label: __("Save Placement"),
			primary_action: async (values) => {
				await frappe.call({
					method: "qd_hrms.performance.update_nine_box_placement",
					args: { calibration: this.data.name, appraisal: row.appraisal, ...values },
					freeze: true,
				});
				dialog.hide();
				await this.load();
			},
		});
		if (!editable) {
			dialog.get_primary_btn().hide();
			dialog.fields_list.forEach((field) => field.df.read_only = 1);
			dialog.refresh();
		}
		dialog.show();
	}

	metric(label, value, tone = "") {
		return `<div class="qd-nine-box-metric ${tone}">
			<div class="qd-nine-box-value">${value}</div><div>${label}</div>
		</div>`;
	}

	empty_state(message) {
		return `<div class="qd-nine-box-empty">${frappe.utils.escape_html(message)}</div>`;
	}
}

(() => {
	const FONT =
		"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap";
	const LOGO = "/assets/qd_hrms/images/qd-logo.png";
	const THEME = "/assets/qd_hrms/css/qd_hrms.css";

	const LIGHT = {
		"--primary": "#0C499C",
		"--primary-color": "#0C499C",
		"--primary-light": "#E8EEF8",
		"--brand-color": "#0C499C",
		"--btn-primary": "#0C499C",
		"--border-primary": "#0C499C",
		"--sidebar-select-color": "#E8EEF8",
		"--fg-hover-color": "#E8EEF8",
		"--awesomplete-hover-bg": "#E8EEF8",
		"--progress-bar-bg": "#0C499C",
		"--checkbox-color": "#0C499C",
		"--checkbox-gradient": "linear-gradient(180deg, #0C499C -124.51%, #0C499C 100%)",
		"--date-active-bg": "#0C499C",
		"--dt-primary-color": "#0C499C",
		"--timeline-badge-color": "#0C499C",
		"--timeline-badge-bg": "#E8EEF8",
		"--alert-text-info": "#0C499C",
		"--alert-bg-info": "#E8EEF8",
		"--bg-blue": "#E8EEF8",
		"--bg-light-blue": "#F3F7FC",
		"--bg-dark-blue": "#C2D2EE",
		"--text-on-blue": "#0C499C",
		"--text-on-light-blue": "#0C499C",
		"--text-on-dark-blue": "#083A7D",
		"--bg-orange": "#FFF3E8",
		"--text-on-orange": "#D8680A",
		"--focus-default": "0 0 0 2px rgba(12, 73, 156, 0.28)",
		"--highlight-shadow": "0 0 0 3px rgba(12, 73, 156, 0.2)",
		"--blue-50": "#F3F7FC",
		"--blue-100": "#E8EEF8",
		"--blue-200": "#D4E0F2",
		"--blue-300": "#C2D2EE",
		"--blue-400": "#5B93E0",
		"--blue-500": "#0C499C",
		"--blue-600": "#0C499C",
		"--blue-700": "#083A7D",
		"--blue-800": "#062E64",
		"--blue-900": "#041F44",
		"--orange-500": "#F67A0D",
		"--orange-600": "#D8680A",
		"--orange-700": "#BD3E0C",
	};

	const DARK = {
		...LIGHT,
		"--primary": "#5B93E0",
		"--primary-color": "#5B93E0",
		"--brand-color": "#5B93E0",
		"--btn-primary": "#0C499C",
		"--sidebar-select-color": "rgba(91, 147, 224, 0.18)",
		"--fg-hover-color": "rgba(91, 147, 224, 0.18)",
	};

	function applyTokens() {
		const dark = document.documentElement.getAttribute("data-theme") === "dark";
		const tokens = dark ? DARK : LIGHT;
		const root = document.documentElement;
		Object.keys(tokens).forEach((key) => {
			root.style.setProperty(key, tokens[key]);
		});
	}

	function loadFont() {
		if (document.getElementById("qd-inter-font")) return;
		const link = document.createElement("link");
		link.id = "qd-inter-font";
		link.rel = "stylesheet";
		link.href = FONT;
		document.head.appendChild(link);
	}

	const CRITICAL = `
header .navbar.navbar-expand, .navbar.navbar-expand, body .navbar {
	background:#fff !important;
	border-bottom:3px solid #f67a0d !important;
	box-shadow:inset 0 -3px 0 #f67a0d !important;
}
.desk-sidebar .standard-sidebar-item.selected,
.desk-sidebar .standard-sidebar-item:hover {
	background-color:#e8eef8 !important;
}
.desk-sidebar .standard-sidebar-item.selected {
	box-shadow:inset 3px 0 0 #f67a0d;
}
.desk-sidebar .standard-sidebar-item.selected > a,
.desk-sidebar .standard-sidebar-item.selected .sidebar-item-label,
.desk-sidebar .standard-sidebar-item:hover > a,
.desk-sidebar .standard-sidebar-item:hover .sidebar-item-label {
	color:#0c499c !important;
}
.widget.links-widget-box .widget-head .widget-label .widget-title,
.widget.shortcut-widget-box .widget-title,
.widget-group .widget-group-title,
.page-head .title-text, .page-title .title-text {
	color:#0c499c !important;
}
.widget.links-widget-box .link-item,
.widget.links-widget-box .link-item .link-content {
	color:#0c499c !important;
}
.widget.links-widget-box .link-item:hover,
.widget.links-widget-box .link-item:hover .link-content {
	color:#f67a0d !important;
}
.btn.btn-primary, .page-head .btn-primary {
	background-color:#0c499c !important;
	border-color:#0c499c !important;
	color:#fff !important;
}`;

	function injectThemeCss() {
		if (!document.getElementById("qd-desk-theme-inline")) {
			const style = document.createElement("style");
			style.id = "qd-desk-theme-inline";
			style.textContent = CRITICAL;
			document.head.appendChild(style);
		}
		if (document.getElementById("qd-desk-theme")) return;
		const link = document.createElement("link");
		link.id = "qd-desk-theme";
		link.rel = "stylesheet";
		link.href = THEME + "?v=" + (window._version_number || Date.now());
		document.head.appendChild(link);
	}

	function setFavicon() {
		let icon = document.querySelector('link[rel="icon"]');
		if (!icon) {
			icon = document.createElement("link");
			icon.rel = "icon";
			document.head.appendChild(icon);
		}
		icon.type = "image/png";
		icon.href = "/assets/qd_hrms/images/qd-favicon.png?v=" + (window._version_number || Date.now());
		document.querySelectorAll('link[rel="shortcut icon"]').forEach((el) => {
			el.type = "image/png";
			el.href = icon.href;
		});
		const theme = document.querySelector('meta[name="theme-color"]');
		if (theme) theme.setAttribute("content", "#0C499C");
	}

	function enhanceNavbar() {
		const brand = document.querySelector(".navbar-brand.navbar-home");
		if (!brand) return;
		brand.setAttribute("href", "/app");
		brand.setAttribute("title", "Quick Delivery — Home");
		let img = brand.querySelector("img.app-logo");
		if (!img) {
			img = document.createElement("img");
			img.className = "app-logo";
			brand.insertBefore(img, brand.firstChild);
		}
		if (!img.getAttribute("src") || !img.getAttribute("src").includes("qd_hrms")) {
			img.src = LOGO;
		}
		img.alt = "Quick Delivery";
	}

	function boot() {
		applyTokens();
		injectThemeCss();
		loadFont();
		setFavicon();
		enhanceNavbar();
	}

	applyTokens();
	injectThemeCss();

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", boot);
	} else {
		boot();
	}

	document.addEventListener("page-change", () => {
		applyTokens();
		enhanceNavbar();
	});

	const observer = new MutationObserver(applyTokens);
	observer.observe(document.documentElement, {
		attributes: true,
		attributeFilter: ["data-theme", "data-theme-mode"],
	});
})();

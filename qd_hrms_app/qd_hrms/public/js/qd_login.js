(() => {
	const SPLASH = "/assets/qd_hrms/images/qd-favicon.png";
	const FAVICON = "/assets/qd_hrms/images/qd-favicon.png";

	// Loaded on every website page, so login-only branding must be gated.
	function isAuthPage() {
		const path = (document.body && document.body.dataset.path) || "";
		if (path === "login") return true;
		return Boolean(
			document.querySelector(".for-login, .login-content, .page-card-head img")
		);
	}

	function setFavicon() {
		let icon = document.querySelector('link[rel="icon"]');
		if (!icon) {
			icon = document.createElement("link");
			icon.rel = "icon";
			document.head.appendChild(icon);
		}
		icon.type = "image/png";
		icon.href = FAVICON + "?v=" + Date.now();
		document.querySelectorAll('link[rel="shortcut icon"]').forEach((el) => {
			el.type = "image/png";
			el.href = icon.href;
		});
	}

	function brandLoginPage() {
		document.body.classList.add("qd-auth-page");
		document.querySelectorAll(".page-card-head img").forEach((img) => {
			if (img.dataset.qdBranded) return;
			img.src = SPLASH;
			img.alt = "Quick Delivery";
			img.dataset.qdBranded = "1";
		});
		document.title = "Login · Quick Delivery";
	}

	function boot() {
		setFavicon();
		if (isAuthPage()) {
			brandLoginPage();
		}
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", boot);
	} else {
		boot();
	}
})();

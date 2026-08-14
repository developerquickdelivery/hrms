(() => {
	const SPLASH = "/assets/qd_hrms/images/qd-splash.png";
	const FAVICON = "/assets/qd_hrms/images/qd-favicon.png";

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

	function brandLoginLogo() {
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
		brandLoginLogo();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", boot);
	} else {
		boot();
	}
})();

(()=>{var k=Object.defineProperty,y=Object.defineProperties;var v=Object.getOwnPropertyDescriptors;var b=Object.getOwnPropertySymbols;var w=Object.prototype.hasOwnProperty,x=Object.prototype.propertyIsEnumerable;var g=(n,r,o)=>r in n?k(n,r,{enumerable:!0,configurable:!0,writable:!0,value:o}):n[r]=o,u=(n,r)=>{for(var o in r||(r={}))w.call(r,o)&&g(n,o,r[o]);if(b)for(var o of b(r))x.call(r,o)&&g(n,o,r[o]);return n},h=(n,r)=>y(n,v(r));(()=>{let n="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap",r="/assets/qd_hrms/images/qd-logo.png",o="/assets/qd_hrms/css/qd_hrms.css",d={"--primary":"#0C499C","--primary-color":"#0C499C","--primary-light":"#E8EEF8","--brand-color":"#0C499C","--btn-primary":"#0C499C","--border-primary":"#0C499C","--sidebar-select-color":"#E8EEF8","--fg-hover-color":"#E8EEF8","--awesomplete-hover-bg":"#E8EEF8","--progress-bar-bg":"#0C499C","--checkbox-color":"#0C499C","--checkbox-gradient":"linear-gradient(180deg, #0C499C -124.51%, #0C499C 100%)","--date-active-bg":"#0C499C","--dt-primary-color":"#0C499C","--timeline-badge-color":"#0C499C","--timeline-badge-bg":"#E8EEF8","--alert-text-info":"#0C499C","--alert-bg-info":"#E8EEF8","--bg-blue":"#E8EEF8","--bg-light-blue":"#F3F7FC","--bg-dark-blue":"#C2D2EE","--text-on-blue":"#0C499C","--text-on-light-blue":"#0C499C","--text-on-dark-blue":"#083A7D","--bg-orange":"#FFF3E8","--text-on-orange":"#D8680A","--focus-default":"0 0 0 2px rgba(12, 73, 156, 0.28)","--highlight-shadow":"0 0 0 3px rgba(12, 73, 156, 0.2)","--blue-50":"#F3F7FC","--blue-100":"#E8EEF8","--blue-200":"#D4E0F2","--blue-300":"#C2D2EE","--blue-400":"#5B93E0","--blue-500":"#0C499C","--blue-600":"#0C499C","--blue-700":"#083A7D","--blue-800":"#062E64","--blue-900":"#041F44","--orange-500":"#F67A0D","--orange-600":"#D8680A","--orange-700":"#BD3E0C"},p=h(u({},d),{"--primary":"#5B93E0","--primary-color":"#5B93E0","--brand-color":"#5B93E0","--btn-primary":"#0C499C","--sidebar-select-color":"rgba(91, 147, 224, 0.18)","--fg-hover-color":"rgba(91, 147, 224, 0.18)"});function i(){let t=document.documentElement.getAttribute("data-theme")==="dark"?p:d,a=document.documentElement;Object.keys(t).forEach(m=>{a.style.setProperty(m,t[m])})}function C(){if(document.getElementById("qd-inter-font"))return;let e=document.createElement("link");e.id="qd-inter-font",e.rel="stylesheet",e.href=n,document.head.appendChild(e)}let E=`
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
}`;function l(){if(!document.getElementById("qd-desk-theme-inline")){let t=document.createElement("style");t.id="qd-desk-theme-inline",t.textContent=E,document.head.appendChild(t)}if(document.getElementById("qd-desk-theme"))return;let e=document.createElement("link");e.id="qd-desk-theme",e.rel="stylesheet",e.href=o+"?v="+(window._version_number||Date.now()),document.head.appendChild(e)}function f(){let e=document.querySelector('link[rel="icon"]');e||(e=document.createElement("link"),e.rel="icon",document.head.appendChild(e)),e.type="image/png",e.href="/assets/qd_hrms/images/qd-favicon.png?v="+(window._version_number||Date.now()),document.querySelectorAll('link[rel="shortcut icon"]').forEach(a=>{a.type="image/png",a.href=e.href});let t=document.querySelector('meta[name="theme-color"]');t&&t.setAttribute("content","#0C499C")}function s(){let e=document.querySelector(".navbar-brand.navbar-home");if(!e)return;e.setAttribute("href","/app"),e.setAttribute("title","Quick Delivery \u2014 Home");let t=e.querySelector("img.app-logo");t||(t=document.createElement("img"),t.className="app-logo",e.insertBefore(t,e.firstChild)),(!t.getAttribute("src")||!t.getAttribute("src").includes("qd_hrms"))&&(t.src=r),t.alt="Quick Delivery"}function c(){i(),l(),C(),f(),s()}i(),l(),document.readyState==="loading"?document.addEventListener("DOMContentLoaded",c):c(),document.addEventListener("page-change",()=>{i(),s()}),new MutationObserver(i).observe(document.documentElement,{attributes:!0,attributeFilter:["data-theme","data-theme-mode"]})})();})();
//# sourceMappingURL=qd_hrms.bundle.D2UGYMVC.js.map

/*
 * site.js: behavior for this site's custom components (the service inquiry dialog).
 * Template behavior stays in main.js. See ../../DESIGN.md.
 */
(function () {
	'use strict';

	var CONTACT_EMAIL = 'ajtparas@gmail.com';
	var TITLES = {
		consulting: 'Data Science Consulting Inquiry',
		automation: 'Automation & App Development Inquiry',
		dashboard: 'Interactive Dashboard Inquiry'
	};
	var REQUIRED = ['clientName', 'clientEmail', 'serviceType', 'projectDescription'];

	var modal = document.getElementById('serviceModal');
	if (!modal) { return; }

	var form = document.getElementById('contactForm');
	var titleEl = document.getElementById('modalTitle');
	var typeEl = document.getElementById('serviceType');
	var statusEl = document.getElementById('formStatus');
	var lastFocus = null;

	function open(service, trigger) {
		lastFocus = trigger || document.activeElement;
		titleEl.textContent = TITLES[service] || 'Service Inquiry';
		typeEl.value = TITLES[service] ? service : '';
		statusEl.textContent = '';
		modal.classList.add('is-open');
		modal.setAttribute('aria-hidden', 'false');
		document.body.style.overflow = 'hidden';
		document.getElementById('clientName').focus();
	}

	function close() {
		modal.classList.remove('is-open');
		modal.setAttribute('aria-hidden', 'true');
		document.body.style.overflow = '';
		form.reset();
		REQUIRED.forEach(function (id) {
			var el = document.getElementById(id);
			el.classList.remove('is-invalid');
			el.removeAttribute('aria-invalid');
		});
		if (lastFocus && lastFocus.focus) { lastFocus.focus(); }
	}

	function field(name) {
		return (new FormData(form).get(name) || '').toString().trim();
	}

	function submit(event) {
		event.preventDefault();
		var valid = true;
		REQUIRED.forEach(function (id) {
			var el = document.getElementById(id);
			var ok = el.value.trim() !== '';
			el.classList.toggle('is-invalid', !ok);
			if (ok) { el.removeAttribute('aria-invalid'); } else { el.setAttribute('aria-invalid', 'true'); }
			valid = valid && ok;
		});
		if (!valid) {
			statusEl.textContent = 'Please fill in the required fields.';
			var firstBad = form.querySelector('.is-invalid');
			if (firstBad) { firstBad.focus(); }
			return;
		}

		var subject = 'Service Inquiry: ' + typeEl.options[typeEl.selectedIndex].text + ' - ' + field('clientName');
		var body = [
			'New service inquiry from ' + field('clientName'),
			'',
			'Name: ' + field('clientName'),
			'Email: ' + field('clientEmail'),
			'Service: ' + typeEl.options[typeEl.selectedIndex].text,
			'',
			'Project description:',
			field('projectDescription'),
			'',
			'Additional notes:',
			field('additionalNotes') || 'None',
			'',
			'Sent from the portfolio website.'
		].join('\n');

		window.location.href = 'mailto:' + CONTACT_EMAIL +
			'?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(body);
		statusEl.textContent = 'Your email app should open with this message filled in. ' +
			'If it does not, email ' + CONTACT_EMAIL + ' directly.';
	}

	// Triggers: any element with data-service opens the dialog.
	document.querySelectorAll('[data-service]').forEach(function (el) {
		el.addEventListener('click', function (event) {
			event.preventDefault();
			open(el.getAttribute('data-service'), el);
		});
	});

	modal.querySelectorAll('[data-close]').forEach(function (el) {
		el.addEventListener('click', close);
	});
	modal.addEventListener('click', function (event) {
		if (event.target === modal) { close(); }
	});
	form.addEventListener('submit', submit);

	document.addEventListener('keydown', function (event) {
		if (!modal.classList.contains('is-open')) { return; }
		if (event.key === 'Escape') { close(); return; }
		if (event.key !== 'Tab') { return; }
		// Keep keyboard focus inside the dialog.
		var focusable = modal.querySelectorAll('button, [href], input, select, textarea');
		var first = focusable[0];
		var last = focusable[focusable.length - 1];
		if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
		else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
	});
})();

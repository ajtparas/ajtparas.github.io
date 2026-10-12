// Runs in the browser on the rendered page. Paste the whole file into the browser tool's JavaScript
// executor (it is a single expression) at each viewport width. It returns measurements, not opinions.
// Text sitting on a background image can't be measured here: those are listed under overImage.
(() => {
	const vw = innerWidth;
	const parse = (c) => {
		const m = c && c.match(/rgba?\(([^)]+)\)/);
		if (!m) return null;
		const p = m[1].split(',').map(parseFloat);
		return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
	};
	const lum = ({ r, g, b }) => {
		const f = (c) => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
		return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
	};
	const ratio = (a, b) => { const la = lum(a), lb = lum(b); return (Math.max(la, lb) + 0.05) / (Math.min(la, lb) + 0.05); };
	const blend = (fg, bg) => ({ r: fg.r * fg.a + bg.r * (1 - fg.a), g: fg.g * fg.a + bg.g * (1 - fg.a), b: fg.b * fg.a + bg.b * (1 - fg.a), a: 1 });
	const bgOf = (el) => {
		for (let e = el; e; e = e.parentElement) {
			const s = getComputedStyle(e);
			if (s.backgroundImage !== 'none') return { image: true };
			const c = parse(s.backgroundColor);
			if (c && c.a > 0.99) return c;
		}
		return { r: 255, g: 255, b: 255, a: 1 };
	};
	const path = (el) => {
		const parts = [];
		for (let e = el; e && e !== document.body && parts.length < 3; e = e.parentElement) {
			parts.unshift(e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (e.classList.length ? '.' + [...e.classList].slice(0, 2).join('.') : ''));
		}
		return parts.join(' > ');
	};
	const visible = (el) => {
		const s = getComputedStyle(el);
		const r = el.getBoundingClientRect();
		return s.visibility !== 'hidden' && s.display !== 'none' && r.width > 0 && r.height > 0 && s.opacity !== '0';
	};

	// Contrast of every element that owns text
	const contrastFails = [], overImage = new Set(), seen = new Set();
	let textNodes = 0;
	document.querySelectorAll('body *').forEach((el) => {
		if (['SCRIPT', 'STYLE', 'NOSCRIPT'].includes(el.tagName) || !visible(el)) return;
		const own = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
		if (!own) return;
		textNodes++;
		const s = getComputedStyle(el);
		const bg = bgOf(el);
		if (bg.image) { overImage.add(path(el)); return; }
		let fg = parse(s.color);
		if (!fg) return;
		if (fg.a < 1) fg = blend(fg, bg);
		const size = parseFloat(s.fontSize), bold = parseInt(s.fontWeight, 10) >= 700;
		const need = size >= 24 || (size >= 18.66 && bold) ? 3 : 4.5;
		const r = ratio(fg, bg);
		if (r < need) {
			const key = path(el) + s.color;
			if (!seen.has(key)) {
				seen.add(key);
				contrastFails.push({ where: path(el), ratio: +r.toFixed(2), need, size: Math.round(size), sample: el.textContent.trim().slice(0, 40) });
			}
		}
	});

	// Tap targets (inline links inside running text are exempt)
	const smallTargets = [];
	document.querySelectorAll('a[href], button, input:not([type=hidden]), select, textarea, [role=button]').forEach((el) => {
		if (!visible(el) || el.getAttribute('aria-hidden') === 'true') return;
		const s = getComputedStyle(el), r = el.getBoundingClientRect();
		if (s.display === 'inline' && el.closest('p, li')) return;
		if (r.width < 44 || r.height < 44) {
			smallTargets.push({ where: path(el), w: Math.round(r.width), h: Math.round(r.height), text: (el.textContent || el.getAttribute('aria-label') || '').trim().slice(0, 30) });
		}
	});

	// Text sizes in use
	const sizes = {};
	document.querySelectorAll('body *').forEach((el) => {
		if (!visible(el) || !([...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim()))) return;
		const px = Math.round(parseFloat(getComputedStyle(el).fontSize) * 10) / 10;
		sizes[px] = (sizes[px] || 0) + 1;
	});

	// Overflow
	const overflow = [];
	if (document.documentElement.scrollWidth > vw + 1) {
		document.querySelectorAll('body *').forEach((el) => {
			const r = el.getBoundingClientRect();
			if (r.right > vw + 1 && r.width > 0 && getComputedStyle(el).position !== 'fixed' && overflow.length < 8) overflow.push(path(el) + ' right=' + Math.round(r.right));
		});
	}

	// Images
	const images = [...document.images].map((im) => {
		const r = im.getBoundingClientRect();
		return { src: decodeURIComponent((im.getAttribute('src') || '').split('/').pop()), natural: im.naturalWidth + 'x' + im.naturalHeight, shown: Math.round(r.width) + 'x' + Math.round(r.height), alt: im.getAttribute('alt'), broken: !im.complete || im.naturalWidth === 0, oversize: r.width ? +(im.naturalWidth / r.width).toFixed(1) : null, lazy: im.loading, aboveFold: r.top < innerHeight };
	}).filter((i) => i.broken || (i.oversize && i.oversize > 2.5) || i.alt === null || (i.aboveFold && i.lazy === 'lazy'));

	// Spacing between cards in the same row (should equal the gap token)
	const cards = [...document.querySelectorAll('.project-card')].map((c) => c.getBoundingClientRect());
	const rowGaps = [];
	cards.forEach((a, i) => cards.forEach((b, j) => { if (j > i && Math.abs(a.top - b.top) < 4 && b.left > a.right) rowGaps.push(Math.round(b.left - a.right)); }));

	return JSON.stringify({
		viewport: vw,
		scrollWidth: document.documentElement.scrollWidth,
		textElements: textNodes,
		contrastFails,
		overImage: [...overImage],
		smallTargets,
		fontSizesPx: sizes,
		overflow,
		imageIssues: images,
		cardRowGapsPx: [...new Set(rowGaps)],
		headings: [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].filter(visible).map((h) => h.tagName + ' ' + h.textContent.trim().slice(0, 40)),
	}, null, 1);
})()

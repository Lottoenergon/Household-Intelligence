/**
 * sanitize.js
 * ---------------------------------------------------------------------------
 * Escaping dan validasi URL untuk SEMUA data yang berasal dari scraping
 * marketplace (judul iklan, nama kawasan, kategori layout, URL listing).
 *
 * Data itu input TIDAK terpercaya: tanpa escaping, judul iklan yang berisi
 * `<img src=x onerror=...>` atau `<script>` akan tereksekusi di halaman karena
 * explorer.js membangun kartu lewat innerHTML. URL juga harus divalidasi
 * skemanya supaya `javascript:` tidak bisa diselipkan ke atribut href.
 * ---------------------------------------------------------------------------
 */
(function () {
    'use strict';

    var HTML_ENTITIES = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
        '`': '&#96;'
    };

    /**
     * Escape teks agar aman disisipkan ke innerHTML (konten maupun atribut).
     * @param {*} value
     * @returns {string}
     */
    function escapeHtml(value) {
        if (value === null || value === undefined) return '';
        return String(value).replace(/[&<>"'`]/g, function (ch) {
            return HTML_ENTITIES[ch];
        });
    }

    /**
     * Normalisasi URL listing dan tolak skema berbahaya.
     * Hanya http/https yang lolos; selain itu mengembalikan '#'.
     * @param {string} url
     * @param {string} [fallbackHost] contoh: 'https://www.rumah123.com'
     * @returns {string} URL absolut yang aman, atau '#'
     */
    function safeExternalUrl(url, fallbackHost) {
        var raw = (url === null || url === undefined) ? '' : String(url).trim();
        if (!raw) return '#';

        var candidate = raw;
        if (raw.indexOf('//') === 0) {
            candidate = 'https:' + raw;                       // protocol-relative
        } else if (!/^[a-z][a-z0-9+.-]*:/i.test(raw)) {
            // Path relatif dari marketplace -> tempel ke host asalnya.
            if (!fallbackHost) return '#';
            candidate = fallbackHost + (raw.charAt(0) === '/' ? raw : '/' + raw);
        }

        try {
            var parsed = new URL(candidate, window.location.origin);
            if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return '#';
            return parsed.href;
        } catch (err) {
            return '#';
        }
    }

    window.escapeHtml = escapeHtml;
    window.safeExternalUrl = safeExternalUrl;
})();

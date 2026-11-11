/* mem20 analytics — cookie-free, no personal data, no cross-site tracking.
 * Shared by: docs/index.html (landing), docs/series/index.html (series hub),
 *            docs/series/comic/index.html, docs/series/chronicles/index.html
 * See docs/series/ANALYTICS.md for what is collected and how to read it.
 */
(function () {
  'use strict';

  /* ---- CONFIG: the one place to change the destination ------------------ */
  var CFG = {
    endpoint: '',            // e.g. 'https://collector.example.com/e' — empty = local only
    site: 'mem20.com',
    respectDNT: true,        // honour DNT / GPC
    trackOutbound: true,
    trackNav: true,
    trackSeries: true
  };
  /* ---------------------------------------------------------------------- */

  var queue = [];

  function dntOn() {
    if (!CFG.respectDNT) return false;
    var d = navigator.doNotTrack || window.doNotTrack || navigator.msDoNotTrack;
    if (d === '1' || d === 'yes' || d === true) return true;
    if (navigator.globalPrivacyControl === true) return true;
    return false;
  }

  function path() {
    // path only: query string and fragment are dropped on purpose
    return location.pathname;
  }

  function refHost() {
    try {
      if (!document.referrer) return '';
      var h = new URL(document.referrer).hostname.replace(/^www\./, '');
      return h === location.hostname.replace(/^www\./, '') ? '' : h;
    } catch (e) { return ''; }
  }

  function send(ev) {
    ev.ts = Date.now();
    ev.site = CFG.site;
    queue.push(ev);
    try {
      document.dispatchEvent(new CustomEvent('mem20:analytics', { detail: ev }));
    } catch (e) { /* no CustomEvent: ignore */ }
    if (!CFG.endpoint) return;
    var body = JSON.stringify(ev);
    try {
      if (navigator.sendBeacon) {
        var ok = navigator.sendBeacon(
          CFG.endpoint,
          new Blob([body], { type: 'application/json' })
        );
        if (ok) return;
      }
    } catch (e) { /* fall through to fetch */ }
    try {
      fetch(CFG.endpoint, {
        method: 'POST',
        body: body,
        headers: { 'Content-Type': 'application/json' },
        keepalive: true,
        mode: 'cors',
        credentials: 'omit'   // never send cookies
      }).catch(function () { /* never surface a network error */ });
    } catch (e) { /* ignore */ }
  }

  function seriesOf(p) {
    if (/\/series\/comic\/?/.test(p)) return 'comic';
    if (/\/series\/chronicles\/?/.test(p)) return 'chronicles';
    if (/\/series\/?$/.test(p)) return 'hub';
    return null;
  }

  function issueNo(el) {
    var issue = el.closest && el.closest('.issue');
    if (!issue) return '';
    var num = issue.querySelector('.num');
    return num ? (num.textContent || '').replace(/[^0-9]/g, '') : '';
  }

  function classify(a) {
    var url;
    try { url = new URL(a.getAttribute('href') || '', location.href); }
    catch (e) { return null; }
    if (!url || !url.href) return null;

    var host = url.hostname.replace(/^www\./, '');
    var self = location.hostname.replace(/^www\./, '');

    if (CFG.trackOutbound) {
      if (host === 'github.com') return { e: 'outbound', d: 'github', u: url.href };
      if (host === 'pypi.org' || host === 'pypi.python.org') return { e: 'outbound', d: 'pypi', u: url.href };
      if (host !== self) return { e: 'outbound', d: 'external', u: url.href };
    }

    var p = url.pathname;
    var inNav = !!(a.closest && a.closest('nav, .nav-links, .foot-links'));

    if (CFG.trackNav && inNav) {
      if (/\/series\/?$/.test(p)) return { e: 'nav', n: 'series', u: p };
      if (/\/series\/comic\/?/.test(p)) return { e: 'nav', n: 'comic', u: p };
      if (/\/series\/chronicles\/?/.test(p)) return { e: 'nav', n: 'chronicles', u: p };
      if (p === '/' || /\/index\.html$/.test(p)) return { e: 'nav', n: 'product', u: p };
    }

    if (CFG.trackSeries) {
      var s = seriesOf(p);
      if (s) return { e: 'series', series: s, i: issueNo(a), u: p };
    }
    return null;
  }

  function onClick(ev) {
    if (ev.defaultPrevented || ev.button !== 0 || ev.metaKey || ev.ctrlKey || ev.shiftKey || ev.altKey) return;
    var t = ev.target;
    if (!t || !t.closest) return;

    // 1. a real link: classify it
    var a = t.closest('a[href]');
    if (a) {
      var hit = classify(a);
      if (hit) {
        hit.p = path();
        hit.t = document.title;
        send(hit);
      }
      return;
    }

    // 2. an issue block with no anchor yet (art not published): still count the
    //    engagement, because "which issue did they open" is the useful signal.
    if (CFG.trackSeries) {
      var issue = t.closest('.issue');
      if (issue) {
        send({
          e: 'series',
          series: seriesOf(path()) || 'comic',
          i: issueNo(t),
          u: path(),
          p: path(),
          t: document.title
        });
      }
    }
  }

  function init() {
    if (dntOn()) {
      window.mem20Analytics = { disabled: 'dnt', queue: queue, config: CFG, track: function () {} };
      return;
    }
    send({ e: 'pageview', p: path(), t: document.title, r: refHost() });
    document.addEventListener('click', onClick, true);
    window.mem20Analytics = {
      queue: queue,
      config: CFG,
      track: function (name, extra) {
        var ev = { e: name, p: path(), t: document.title };
        if (extra) for (var k in extra) if (Object.prototype.hasOwnProperty.call(extra, k)) ev[k] = extra[k];
        send(ev);
      }
    };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();

(function () {
  'use strict';

  var KEY = 'mem20_exp_gh_exp_001_arm_v1';

  function hashString(str) {
    var h = 2166136261;
    for (var i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h += (h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24);
    }
    return (h >>> 0);
  }

  function getOrAssign(visitorKey) {
    try {
      var existing = localStorage.getItem(KEY);
      if (existing === 'A' || existing === 'B') return existing;
    } catch (e) { /* storage unavailable */ }

    var seed = visitorKey;
    if (!seed) {
      // privacy-respecting local seed: random, stored locally only
      seed = String(Date.now()) + ':' + String(Math.random()).slice(2);
    }
    var arm = (hashString(seed) % 2 === 0) ? 'A' : 'B';
    try { localStorage.setItem(KEY, arm); } catch (e) { /* ignore */ }
    return arm;
  }

  function assignAndTrack(visitorKey) {
    var code = getOrAssign(visitorKey);
    var arm = code === 'B' ? 'treatment' : 'control';
    try {
      window.__ghExp001Visitor = { experiment: 'GH-EXP-001', arm: arm, arm_code: code, mode: 'per_visitor' };
      if (window.mem20Analytics && typeof window.mem20Analytics.track === 'function') {
        window.mem20Analytics.track('experiment_assignment', {
          experiment: 'GH-EXP-001',
          arm: arm,
          arm_code: code,
          assignment_mode: 'per_visitor'
        });
      } else {
        document.addEventListener('DOMContentLoaded', function () {
          if (window.mem20Analytics && typeof window.mem20Analytics.track === 'function') {
            window.mem20Analytics.track('experiment_assignment', {
              experiment: 'GH-EXP-001',
              arm: arm,
              arm_code: code,
              assignment_mode: 'per_visitor'
            });
          }
        }, { once: true });
      }
    } catch (e) { /* never block rendering */ }
    return { arm: arm, arm_code: code };
  }

  function autoInit() {
    try {
      var meta = document.querySelector('meta[name="gh-exp-001-per-visitor"]');
      var enabled = meta ? meta.getAttribute('content') !== 'off' : true;
      if (enabled) assignAndTrack();
    } catch (e) { /* ignore */ }
  }

  window.GHExp001PerVisitor = { assignAndTrack: assignAndTrack, getOrAssign: getOrAssign };
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoInit, { once: true });
  } else {
    autoInit();
  }
})();

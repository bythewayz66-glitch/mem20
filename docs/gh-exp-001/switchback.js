(function () {
  'use strict';

  function utcDayKey(d) {
    var dt = d ? new Date(d) : new Date();
    return dt.toISOString().slice(0, 10);
  }

  async function loadSchedule(url) {
    var res = await fetch(url, { cache: 'no-store', credentials: 'omit' });
    if (!res.ok) throw new Error('schedule load failed: ' + res.status);
    return res.json();
  }

  function pickArm(schedule, dayKey) {
    var assignments = (schedule && schedule.assignments) || {};
    var code = assignments[dayKey] || 'A';
    var arms = (schedule && schedule.arms) || { A: 'control', B: 'treatment' };
    return { day: dayKey, code: code, arm: arms[code] || (code === 'B' ? 'treatment' : 'control') };
  }

  function announce(selection, source) {
    try {
      window.__ghExp001 = { experiment: 'GH-EXP-001', selection: selection, source: source };
      document.documentElement.setAttribute('data-gh-exp-001-arm', selection.arm);
      document.documentElement.setAttribute('data-gh-exp-001-day', selection.day);
      if (window.mem20Analytics && typeof window.mem20Analytics.track === 'function') {
        window.mem20Analytics.track('experiment_assignment', {
          experiment: 'GH-EXP-001',
          arm: selection.arm,
          arm_code: selection.code,
          day: selection.day,
          assignment_mode: 'day_switchback'
        });
      } else {
        document.addEventListener('mem20:analytics', function once() {
          document.removeEventListener('mem20:analytics', once);
          if (window.mem20Analytics && typeof window.mem20Analytics.track === 'function') {
            window.mem20Analytics.track('experiment_assignment', {
              experiment: 'GH-EXP-001',
              arm: selection.arm,
              arm_code: selection.code,
              day: selection.day,
              assignment_mode: 'day_switchback'
            });
          }
        }, { once: true });
      }
    } catch (e) { /* never block rendering */ }
  }

  async function activate(opts) {
    opts = opts || {};
    var scheduleUrl = opts.scheduleUrl || 'gh-exp-001/schedule.json';
    var schedule = await loadSchedule(scheduleUrl);
    var selection = pickArm(schedule, utcDayKey());
    announce(selection, scheduleUrl);

    if (selection.arm === 'treatment' && typeof opts.onTreatment === 'function') {
      opts.onTreatment(selection, schedule);
    } else if (selection.arm === 'control' && typeof opts.onControl === 'function') {
      opts.onControl(selection, schedule);
    }
    return selection;
  }

  window.GHExp001Switchback = { utcDayKey: utcDayKey, loadSchedule: loadSchedule, pickArm: pickArm, activate: activate };
})();

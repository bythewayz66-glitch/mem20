"""Ecosystem peer integrations and absorbed-member aggregation for mem20pipez."""
from __future__ import annotations
from typing import Any, Dict

def _absorbed_member_peers():
    try:
        import importlib, importlib.util, pathlib, sys
        repo = pathlib.Path(__file__).resolve()
        root = None
        for par in repo.parents:
            if (par / '_mem20_absorbed_finder.py').exists():
                root = par
                break
        if root is None:
            root = pathlib.Path(__file__).resolve().parents[2] if len(pathlib.Path(__file__).resolve().parents) > 2 else pathlib.Path(__file__).resolve().parent
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        try:
            import _mem20_absorbed_finder  # noqa: F401
        except Exception:
            pass
        tc = root / 'toolchest' / 'src'
        if tc.is_dir() and str(tc) not in sys.path:
            sys.path.insert(0, str(tc))
        target_dir = None
        for parent in [pathlib.Path(__file__).resolve().parent, pathlib.Path(__file__).resolve().parents[1] if len(pathlib.Path(__file__).resolve().parents)>1 else None, pathlib.Path(__file__).resolve().parents[2] if len(pathlib.Path(__file__).resolve().parents)>2 else None]:
            if parent is None:
                continue
            if (parent / 'absorbed').is_dir():
                target_dir = parent
                break
        if target_dir is None:
            return {'ok': True, 'members_with_ecosystem_probe': 0, 'members_ok': 0, 'peer_checks_total': 0, 'checks': {}}
        adir = target_dir / 'absorbed'
        members = sorted(p.name for p in adir.iterdir() if p.is_dir() and p.name.startswith('mem20') and p.name.endswith('z')) if adir.is_dir() else []
        checks = {}
        total = 0
        okm = 0

        def count_from_report(r):
            if not isinstance(r, dict):
                return 1, bool(r)
            for key in ('checks', 'integrations', 'peers', 'edges'):
                v = r.get(key)
                if isinstance(v, dict):
                    return len(v), bool(r.get('ok', True))
                if isinstance(v, list):
                    return len(v), bool(r.get('ok', True))
            if isinstance(r.get('reachable'), list):
                c = len(r.get('checks') or {})
                if c:
                    return c, bool(r.get('ok', True))
                return len(r.get('reachable')), bool(r.get('ok', len(r.get('reachable'))>0))
            c = r.get('count')
            if isinstance(c, int):
                return c, bool(r.get('ok', c>0))
            integration_keys = {'path_scripts','toolchest_total','dedup_probe_seen','focus_probe','engine_status_checked','memory','toolchest','sitemapz','webhook','cliz','verify','ops','corez','kanban'}
            found = [k for k in r.keys() if k in integration_keys]
            if found:
                return len(found), True
            return 0, bool(r.get('ok', False))

        for name in members:
            try:
                eco = importlib.import_module(f"{name}.ecosystem")
                if hasattr(eco, 'probe'):
                    r = eco.probe()
                    c, ok = count_from_report(r)
                    checks[name] = {'ok': bool(r.get('ok', ok)) if isinstance(r, dict) else bool(ok), 'count': int(c), 'source': 'ecosystem.probe'}
                    total += int(c)
                    if checks[name]['ok']:
                        okm += 1
                    continue
                fns = [x for x in dir(eco) if not x.startswith('_') and callable(getattr(eco, x))]
                if fns:
                    checks[name] = {'ok': True, 'count': len(fns), 'source': 'ecosystem.callables'}
                    total += len(fns); okm += 1
                    continue
            except Exception as e:
                eco_err = f"{type(e).__name__}: {e}"
            else:
                eco_err = None
            try:
                dom = importlib.import_module(f"{name}.domain")
                for fn_name in ('probe', 'estate_context', 'doctor', 'status'):
                    fn = getattr(dom, fn_name, None)
                    if callable(fn):
                        try:
                            r = fn()
                        except TypeError:
                            try:
                                r = fn(None)
                            except Exception:
                                continue
                        except Exception:
                            continue
                        c, ok = count_from_report(r)
                        if fn_name == 'estate_context' and c == 0 and isinstance(r, dict) and r:
                            c = len([k for k in r.keys() if not k.startswith('_')])
                        if c > 0:
                            checks[name] = {'ok': bool(ok), 'count': int(c), 'source': f'domain.{fn_name}'}
                            total += int(c)
                            if checks[name]['ok']:
                                okm += 1
                            break
                else:
                    if name not in checks:
                        checks[name] = {'ok': False, 'count': 0, 'error': eco_err or 'no_peer_surface'}
            except Exception as e:
                if name not in checks:
                    checks[name] = {'ok': False, 'count': 0, 'error': eco_err or f"{type(e).__name__}: {e}"}
        return {'ok': True, 'members_with_ecosystem_probe': len(members), 'members_ok': okm, 'peer_checks_total': total, 'checks': checks}
    except Exception as e:
        return {'ok': False, 'members_with_ecosystem_probe': 0, 'members_ok': 0, 'peer_checks_total': 0, 'error': f"{type(e).__name__}: {e}", 'checks': {}}


def _safe(name, fn):
    try:
        r = fn() or {}
        if isinstance(r, dict):
            return {'subsystem': name, **r} if 'subsystem' not in r else r
        return {'ok': True, 'subsystem': name, 'result': r}
    except Exception as e:
        return {'ok': False, 'subsystem': name, 'error': f"{type(e).__name__}: {e}"}

def _core_peers():
    checks = {}
    def memory_peer():
        try:
            from memory_engine import memory
            rows = memory.recall(k=1)
            return {'ok': True, 'count': len(rows) if isinstance(rows, list) else 0}
        except Exception as e:
            return {'ok': False, 'error': f"{type(e).__name__}: {e}"}
    checks['memory_engine'] = _safe('memory_engine', memory_peer)

    def toolchest_peer():
        try:
            from toolchest.catalog import load_inventory
            inv = load_inventory()
            total = inv.get('total') if isinstance(inv, dict) else None
            if total is None and isinstance(inv, dict):
                counts = inv.get('counts') or {}
                total = counts.get('total')
            return {'ok': True, 'total': total}
        except Exception as e:
            return {'ok': False, 'error': f"{type(e).__name__}: {e}"}
    checks['toolchest'] = _safe('toolchest', toolchest_peer)

    def path_peer():
        try:
            import mem20path
            scripts = mem20path.discover_scripts() if hasattr(mem20path, 'discover_scripts') else {}
            n = len(scripts) if isinstance(scripts, dict) else 0
            return {'ok': True, 'scripts': n}
        except Exception as e:
            return {'ok': False, 'error': f"{type(e).__name__}: {e}"}
    checks['mem20path'] = _safe('mem20path', path_peer)

    def sitemap_peer():
        try:
            from mem20sitemapz.policy import is_skipped_dir
            v = is_skipped_dir('.git')
            return {'ok': True, 'skips_git': bool(v)}
        except Exception as e:
            return {'ok': False, 'error': f"{type(e).__name__}: {e}"}
    checks['mem20sitemapz'] = _safe('mem20sitemapz', sitemap_peer)

    def webhook_peer():
        try:
            from mem20webhooksupernetworkz.domain import DeliveryLedger
            ledger = DeliveryLedger(max_entries=4)
            ledger.add('peer-probe')
            return {'ok': True, 'dedup_probe_seen': 'peer-probe' in ledger}
        except Exception as e:
            return {'ok': False, 'error': f"{type(e).__name__}: {e}"}
    checks['mem20webhooksupernetworkz'] = _safe('mem20webhooksupernetworkz', webhook_peer)

    def cliz_peer():
        try:
            import mem20cliz
            sv = getattr(mem20cliz, 'SCHEMA_VERSION', None)
            return {'ok': True, 'schema_version': sv}
        except Exception as e:
            return {'ok': False, 'error': f"{type(e).__name__}: {e}"}
    checks['mem20cliz'] = _safe('mem20cliz', cliz_peer)

    return checks



def probe(include_member_ecosystems: bool = True) -> dict:
    checks = _core_peers()
    reachable = [k for k, v in checks.items() if v.get('ok')]
    result = {
        'ok': len(reachable) >= 6,
        'count': len(reachable),
        'core_count': len(checks),
        'reachable': reachable,
        'checks': checks,
    }
    if include_member_ecosystems:
        amp = _absorbed_member_peers()
        result['member_ecosystems'] = amp
        result['peer_surface_total'] = int(result['core_count']) + int(amp.get('peer_checks_total', 0))
        result['count'] = result['peer_surface_total']
    return result

"""Replay only registered development inputs and explain retained branch issues.

Native output tuples are observed. Intermediate rounding is reconstructed from
core.reference and checked against exact nearest-even rounding, not instrumented C.
Original evidence is read-only; run identity goes to ignored build/branch-use/.
"""
import csv
from fractions import Fraction as Q
import json
import platform
import struct
import subprocess
import sys

import numpy as np
from core import intent, reference
from qualify import ROOT, compiled, sha


def bits(value):
    return struct.pack('>f', float(value)).hex()


def rounded_operations(x, u, dt, cfg, limit):
    operations = []

    def op(name, exact):
        value = np.float32(float(exact))
        represented = Q(float(value))
        neighbors = [np.nextafter(value, np.float32(-np.inf)),
                     np.nextafter(value, np.float32(np.inf))]
        error = abs(represented-exact)
        for neighbor in neighbors:
            distance = abs(Q(float(neighbor))-exact)
            assert error <= distance, 'not nearest binary32'
            if error == distance:
                assert int(bits(value), 16) % 2 == 0, 'tie did not round to even'
        operations.append(dict(operation=name, exact_before_rounding=str(exact),
                               binary32=str(represented), bits_hex=bits(value),
                               signed_rounding_error=str(represented-exact)))
        return represented

    x, u, dt = map(Q, (float(x), u, dt))
    denominator = op('tau + dt', Q(cfg['tau'])+dt)
    alpha = op('dt / rounded_denominator', dt/denominator)
    difference = op('u - x', u-x)
    delta = op('rounded_alpha * rounded_difference', alpha*difference)
    lo = op('-slew_down * dt', -Q(cfg['slew_down'])*dt)
    hi = op('slew_up * dt', Q(cfg['slew_up'])*dt)
    reached = op('x + clipped_delta', x+max(lo, min(hi, delta)))
    flag = lambda v, low, high: -1 if v < low else 1 if v > high else 0
    output = max(-Q(limit), min(Q(limit), reached)), flag(delta, lo, hi), flag(reached, -limit, limit)
    return operations, delta, reached, output


def main():
    spec = json.loads((ROOT/'spec.json').read_text())
    registration = json.loads((ROOT/'registration.json').read_text())
    for filename in ('spec.json', 'traces.json'):
        assert sha(ROOT/filename) == registration['sha256'][filename]
    baseline = json.loads((ROOT/'evidence/results.json').read_text())
    traces = json.loads((ROOT/'traces.json').read_text())
    with (ROOT/'evidence/traces.csv').open() as stream:
        retained = list(csv.DictReader(stream))
    flagged = {(r['variant'], r['trace'], r['step']): r['issues']
               for r in baseline['branch_requirement_issues']}
    build = ROOT/'build/branch-use'
    build.mkdir(parents=True, exist_ok=True)
    local = Q(spec['numerics']['local_error_coefficient'])*Q(spec['numerics']['unit_roundoff'])
    limit = Q(spec['domain']['state_abs_max'])
    cases, builds, observed_keys = [], {}, []
    count = disagreements = 0
    for name, cfg in spec['variants'].items():
        run, builds[name] = compiled(name, spec, build)
        for trace in traces:
            exact = Q(trace['initial'])
            state = float(exact)
            bound = Q(0)
            for step, sample in enumerate(trace['steps']):
                u, dt, reset = (sample[k] for k in ('u', 'dt', 'reset'))
                expected = intent(exact, u, dt, reset, cfg, limit)
                ref = reference(state, u, dt, reset, cfg, limit)
                native = run(state, u, dt, reset)
                assert struct.pack('3f', *ref) == struct.pack('3f', *native)
                disagreements += tuple(expected[1:]) != tuple(native[1:])
                previous_bound = bound
                bound = Q(0) if reset else bound+(local if dt else 0)
                row = retained[count]
                key = name, trace['name'], step
                assert (row['variant'], row['trace'], int(row['step'])) == key
                assert float(row['c_rad_s']) == native[0]
                assert float(row['intent_rad_s']) == float(expected[0])
                assert float(row['bound_rad_s']) == float(bound)
                count += 1
                comparisons = []
                if not reset and dt:
                    alpha = Q(dt)/(Q(cfg['tau'])+Q(dt))
                    delta = alpha*(Q(u)-exact)
                    lo, hi = -Q(cfg['slew_down'])*Q(dt), Q(cfg['slew_up'])*Q(dt)
                    reached = exact+max(lo, min(hi, delta))
                    # Independent target/projection form must recover the same state.
                    assert max(-limit, min(limit, reached)) == expected[0]
                    for label, center, radius, low, high in (
                        ('slew', delta, alpha*previous_bound+local, lo, hi),
                        ('rate clamp', reached, bound, -limit, limit),
                    ):
                        for operator, threshold in (('<', low), ('>', high)):
                            if abs(center-threshold) <= radius:
                                comparisons.append(dict(kind=label, operator=operator,
                                    threshold_rad_s=str(threshold), center_rad_s=str(center),
                                    radius_rad_s=str(radius),
                                    interval_rad_s=[str(center-radius), str(center+radius)]))
                assert bool(comparisons) == (row['branch_issue'] == 'True') == (key in flagged)
                if comparisons:
                    observed_keys.append(key)
                    assert sorted(set(('slew branch' if c['kind'] == 'slew' else c['kind'])+' interval touches threshold' for c in comparisons)) == sorted(flagged[key])
                    operations, fdelta, freached, reconstructed = rounded_operations(state, u, dt, cfg, limit)
                    assert tuple(map(float, reconstructed)) == native
                    # For these exposed cases, the uncertain comparison is an exact tie
                    # in both arithmetic paths. This assertion is not a general claim.
                    for comparison in comparisons:
                        operand = fdelta if comparison['kind'] == 'slew' else freached
                        assert Q(comparison['center_rad_s']) == Q(comparison['threshold_rad_s']) == operand
                        comparison.update(binary32_operand_rad_s=str(operand),
                                          exact_predicate=False, binary32_predicate=False)
                    cases.append(dict(variant=name, trace=trace['name'], step=step,
                        input=dict(prior_exact_rad_s=str(exact), prior_c_rad_s=str(Q(state)),
                                   u_rad_s=str(Q(u)), dt_s=str(Q(dt)), reset=reset),
                        comparisons=comparisons, rounding=operations,
                        exact_output=[str(v) for v in expected],
                        native_output=list(native), native_output_bits=[bits(v) for v in native],
                        classification='conservative interval touch; reconstructed threshold tie; no branch disagreement'))
                exact, state = expected[0], native[0]
    assert len(retained) == count == baseline['evaluated_steps']
    assert disagreements == baseline['branch_disagreements']
    assert set(observed_keys) == set(flagged)
    files = ['spec.json', 'registration.json', 'traces.json', 'core.py', 'generate.py',
             'qualify.py', 'review_branch_use.py', 'evidence/results.json', 'evidence/traces.csv',
             'generated/zero_reset.c', 'generated/tracking_reset.c']
    result = dict(status='development branch-use replay complete; external consumer requirements unresolved',
                  evaluated_steps=count, reviewed_issue_steps=len(cases),
                  observed_branch_disagreements=disagreements,
                  intermediate_values='source reconstruction; native output tuples directly observed',
                  nearest_even_checks='exact rational distances to adjacent binary32 values for each recorded operation',
                  contract_changed=False, integration_qualified=False, withheld_executed=False,
                  sha256={f: sha(ROOT/f) for f in files}, cases=cases)
    (ROOT/'evidence/branch-use.json').write_text(json.dumps(result, indent=2)+'\n')
    lines = ['<!-- Generated by review_branch_use.py from branch-use.json. -->',
             '# Executed branch detail', '',
             'Source: [branch-use.json](branch-use.json). Steps are zero-based. Intervals are',
             'conservative numerical bounds, not confidence intervals. Each predicate below',
             'is false in exact intent and the reconstructed binary32 path; native output',
             'tuples agree. Output order: state (rad/s), slew flag, clamp flag.', '',
             '| Variant / trace | Step | Uncertain predicate | Interval (rad/s) | Native output |',
             '| :--- | ---: | :--- | :--- | :--- |']
    for case in result['cases']:
        for c in case['comparisons']:
            operand = 'delta' if c['kind'] == 'slew' else 'reached'
            lines.append(f"| {case['variant']} / {case['trace']} | {case['step']} | "
                         f"{operand} {c['operator']} {c['threshold_rad_s']} | "
                         f"[{', '.join(c['interval_rad_s'])}] | "
                         f"{', '.join(str(Q(v)) for v in case['native_output'])} |")
    (ROOT/'evidence/branch-use-table.md').write_text('\n'.join(lines)+'\n')
    identity = dict(builds=builds, python=sys.version, numpy=np.__version__, platform=platform.platform(),
                    compiler=subprocess.check_output(['cc', '--version'], text=True).strip(),
                    report_sha256=sha(ROOT/'evidence/branch-use.json'))
    (build/'run.json').write_text(json.dumps(identity, indent=2)+'\n')
    print(f"Replayed {count} existing steps; reviewed {len(cases)} flagged steps; {disagreements} branch disagreements.")


if __name__ == '__main__':
    main()

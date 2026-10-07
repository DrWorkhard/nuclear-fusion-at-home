"""Fixed C-then-J execution order and budgets for the trusted native operations.

Operations own process-group supervision and source/receipt validation. This
module supplies their absolute deadlines, never fresh per-operation allowances.
The native adapter supplies supervised operations; execution requires a reviewed lock.
"""
import time
from dataclasses import dataclass

from fusion_baselines import joint_decision as decision
from fusion_baselines import joint_equilibrium as solver

SEARCH_SECONDS, DIAGNOSTIC_SECONDS, FIT_SECONDS = 1800, 900, 300


class ArmInterrupted(RuntimeError):
    """Resource, source or operation failure; never a completed numerical rejection."""


@dataclass(frozen=True)
class Window:
    monotonic: float
    wall: float


class Arm:
    def __init__(self, output, name):
        self.started, self.wall_started = time.monotonic(), time.time()
        self.output, self.name = output, name
        self.search = Window(self.started+SEARCH_SECONDS, self.wall_started+SEARCH_SECONDS)
        self.diagnostic = None
        self.events = []
        output.mkdir(exist_ok=False)
        if solver.shutil.disk_usage(output).free < solver.START_RESERVE:
            raise ArmInterrupted('initial disk reserve')
        self.guard(self.search)

    def guard(self, window):
        elapsed = time.monotonic()-self.started
        wall_elapsed = time.time()-self.wall_started
        if abs(elapsed-wall_elapsed) > 5:
            raise ArmInterrupted('arm-wide clock disagreement')
        reason = solver.stop_reason(self.output, window.monotonic, window.wall)
        if reason:
            raise ArmInterrupted(reason)

    def event(self, name):
        self.events.append(dict(event=name, monotonic=time.monotonic(), wall=time.time()))
        solver.save(self.output/'schedule.json', dict(arm=self.name, events=self.events,
            search_deadline=dict(monotonic=self.search.monotonic, wall=self.search.wall),
            diagnostic_deadline=None if self.diagnostic is None else dict(
                monotonic=self.diagnostic.monotonic, wall=self.diagnostic.wall)))

    def fit_window(self):
        self.guard(self.search)
        if self.name == 'C':
            return self.search
        mono, wall = time.monotonic(), time.time()
        if min(self.search.monotonic-mono, self.search.wall-wall) < FIT_SECONDS:
            raise ArmInterrupted('less than 300 search seconds remain for joint fit')
        return Window(mono+FIT_SECONDS, wall+FIT_SECONDS)

    def begin_diagnostics(self):
        if self.diagnostic is not None:
            raise ArmInterrupted('diagnostic budget already started')
        mono, wall = time.monotonic(), time.time()
        # C's ordinary cap can finish an in-flight call and serialize its earlier
        # eligible candidate. This overrun consumes diagnostics, never extra time.
        self.diagnostic = Window(min(mono, self.search.monotonic)+DIAGNOSTIC_SECONDS,
                                 min(wall, self.search.wall)+DIAGNOSTIC_SECONDS)
        self.guard(self.diagnostic)
        self.event('diagnostic-budget-start')
        return self.diagnostic


def checked_fit(operations, arm, proposal, solved, training):
    """Normal cap proof comes from supervised operations, not a generic TimeoutError."""
    window = arm.fit_window()
    outer = (Window(arm.search.monotonic+DIAGNOSTIC_SECONDS,
                    arm.search.wall+DIAGNOSTIC_SECONDS) if arm.name == 'C' else arm.search)
    arm.event(f'{proposal}-fit-start')
    arm.guard(window)
    result = operations.fit(arm, proposal, solved, training, window, outer)
    arm.guard(outer)
    if result['window'] != window or result['stop'] not in ('solver-return', 'fit-cap'):
        raise ArmInterrupted('unverified fit stop')
    ordinary = result['stop'] == 'fit-cap'
    if ordinary:
        if max(time.monotonic()-window.monotonic, time.time()-window.wall) < 0:
            raise ArmInterrupted('fit cap claimed before its deadline')
        if (result['search']['status']['reason'] != 'budget'
                or not decision.fit_eligible(result['search'], True)):
            raise ArmInterrupted('fit cap without completed startup and eligible candidate')
    elif result['search']['status']['reason'] != 'solver-return':
        raise ArmInterrupted('contradictory fit completion')
    else:
        arm.guard(window)
    if not result['search']['startup_pass']:
        raise ArmInterrupted('fit startup failed')
    if arm.name == 'J' or not ordinary:
        arm.guard(arm.search)
    arm.event(f'{proposal}-fit-finished')
    return dict(result, ordinary_fit_cap=ordinary)


def checked_diagnostics(operations, arm, frozen):
    arm.guard(arm.diagnostic)
    arm.event('diagnostics-start')
    arm.guard(arm.diagnostic)
    report = operations.diagnose(arm, frozen, arm.diagnostic)
    arm.guard(arm.diagnostic)
    operations.verify(arm)
    arm.guard(arm.diagnostic)
    if not report['completed'] or report['selection_sha256'] != frozen['selection_sha256']:
        raise ArmInterrupted('incomplete or mixed selected diagnostics')
    report = dict(report, budget_complete=True)
    arm.event('diagnostics-finished')
    arm.guard(arm.diagnostic)
    return dict(frozen=frozen, diagnostics=report)


def control_arm(operations, arm):
    operations.setup(arm, arm.search)
    arm.guard(arm.search)
    arm.event('control-training-start')
    arm.guard(arm.search)
    training = operations.score(arm, 'control', None, arm.search)
    arm.guard(arm.search)
    decision.complete_score(training, 'training')
    fit = checked_fit(operations, arm, 'control', None, training)
    if not decision.fit_eligible(fit['search'], fit['ordinary_fit_cap']):
        raise ArmInterrupted('no eligible control candidate')
    # Budget accounting starts here, but no validation is requested until the
    # selection write has returned successfully and sources are checked again.
    arm.begin_diagnostics()
    frozen = operations.freeze(arm, 'control', None, training, fit, arm.diagnostic)
    arm.guard(arm.diagnostic)
    arm.event('selection-frozen')
    return checked_diagnostics(operations, arm, frozen)


def joint_arm(operations, arm):
    operations.setup(arm, arm.search)
    arm.guard(arm.search)
    proposals, fits, solves = [], {}, {}
    for proposal in ('plus', 'minus'):
        arm.guard(arm.search)
        arm.event(f'{proposal}-solve-start')
        arm.guard(arm.search)
        solved = operations.solve(arm, proposal, arm.search)
        arm.guard(arm.search)
        if not solved['completed']:
            raise ArmInterrupted('unfinished equilibrium operation')
        solves[proposal] = solved
        row = dict(proposal=proposal, completed=False, rejection=solved.get('rejection'),
                   training=None, search=None, ordinary_fit_cap=False)
        if row['rejection'] is not None:
            decision.numerical_rejection(row)
        else:
            arm.event(f'{proposal}-training-start')
            arm.guard(arm.search)
            training = operations.score(arm, proposal, solved, arm.search)
            arm.guard(arm.search)
            row['training'] = training
            if training['completed'] and not training['eligible']:
                row['rejection'] = dict(kind='plasma-domain', evidence=dict(
                    proposal=proposal, input_sha256=decision.target.INPUT_HASHES[proposal],
                    completed=True, resource_interrupted=False, result=training))
                decision.numerical_rejection(row)
            else:
                decision.complete_score(training, 'training')
                fitted = checked_fit(operations, arm, proposal, solved, training)
                fits[proposal] = fitted
                row.update(search=fitted['search'], ordinary_fit_cap=fitted['ordinary_fit_cap'])
        arm.guard(arm.search)
        row['completed'] = True
        proposals.append(row)
        operations.save_proposal(arm, row)
        arm.guard(arm.search)
        arm.event(f'{proposal}-finished')
    operations.verify(arm)
    arm.guard(arm.search)
    selected = decision.select_joint(proposals)
    if selected is None:
        return proposals, None
    row = proposals[selected]
    frozen = operations.freeze(arm, row['proposal'], solves[row['proposal']], row['training'],
                               fits[row['proposal']], arm.search)
    arm.guard(arm.search)
    arm.event('selection-frozen')
    arm.begin_diagnostics()
    return proposals, checked_diagnostics(operations, arm, frozen)


def run(operations, output):
    """One nonadaptive attempt. Any interruption stops; no retry or budget reset."""
    output.mkdir(exist_ok=False)
    result = dict(completed=False, verdict='inconclusive', physical_admission=False,
                  actual_coil_endpoint=None, full_joint_execution_enabled=False, arms=[])
    try:
        control = Arm(output/'C', 'C')
        result['arms'].append('C')
        c = control_arm(operations, control)
        # A completed but unusable C diagnostic is already inconclusive. Do not
        # spend another arm's budget when the registered paired result is absent.
        decision.diagnostic_summary(c['frozen'], c['diagnostics'])
        control.guard(control.diagnostic)
        joint = Arm(output/'J', 'J')
        result['arms'].append('J')
        proposals, j = joint_arm(operations, joint)
        result.update(decision.assess(proposals, c, j))
        # Final hashes and serialization belong to the remaining active window.
        active = joint.diagnostic or joint.search
        operations.verify(control)
        operations.verify(joint)
        joint.guard(active)
        solver.save(output/'comparison.json', result)
        joint.guard(active)
        return result
    except (ArmInterrupted, decision.IncompleteComparison) as exc:
        result.update(completed=False, verdict='inconclusive', reason=str(exc))
    except Exception as exc:
        # Software errors also preserve a bounded incomplete result; never infer
        # numerical rejection from an exception's general Python type or text.
        result.update(completed=False, verdict='inconclusive',
                      error=f'{type(exc).__name__}: {exc}')
    solver.save(output/'comparison.json', result)
    return result

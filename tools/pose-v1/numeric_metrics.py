"""Approved preprocessing gates; also runs with the board's standard library."""
import math

POLICY = {
    'amplitude_atol': 1e-6,
    'amplitude_rtol': 1e-6,
    'phase_circular_max_rad': 1e-5,
    'phase_scalar_review_rad': 1e-5,
    'artificial_pi_boundary_blocking': False,
}


def compare_tokens(actual, reference, bitwise_equal):
    if len(actual) != 10800 or len(reference) != 10800:
        raise ValueError('Expected [1,180,60] tensor')
    if not all(math.isfinite(float(v)) for v in (*actual, *reference)):
        raise ValueError('Non-finite actual/reference tensor')
    amp, phase, circular, differences = [], [], [], []
    amp_violations = 0
    for index, (a, b) in enumerate(zip(actual, reference)):
        delta = float(a) - float(b)
        error = abs(delta)
        differences.append(error)
        if index % 60 < 30:
            amp.append(error)
            amp_violations += error > POLICY['amplitude_atol'] + POLICY['amplitude_rtol'] * abs(float(b))
        else:
            phase.append(error)
            circular.append(abs(math.atan2(math.sin(delta), math.cos(delta))))
    return {
        'finite': True,
        'max_abs': max(differences),
        'mean_abs': math.fsum(differences) / len(differences),
        'different_elements': sum(v != 0 for v in differences),
        'bitwise_equal': bool(bitwise_equal),
        'amplitude_max_abs': max(amp),
        'amplitude_mean_abs': math.fsum(amp) / len(amp),
        'amplitude_violations': amp_violations,
        'amplitude_pass': amp_violations == 0,
        'phase_scalar_max_abs_rad': max(phase),
        'phase_scalar_mean_abs_rad': math.fsum(phase) / len(phase),
        'phase_circular_max_rad': max(circular),
        'phase_circular_rms_rad': math.sqrt(math.fsum(v*v for v in circular) / len(circular)),
        'phase_circular_violations': sum(v > POLICY['phase_circular_max_rad'] for v in circular),
        'phase_circular_pass': max(circular) <= POLICY['phase_circular_max_rad'],
        'scalar_review_required': max(phase) > POLICY['phase_scalar_review_rad'],
    }


def gate_result(kind, metrics):
    numerical_pass = metrics['amplitude_pass'] and metrics['phase_circular_pass']
    if kind == 'artificial_pi_boundary':
        return {'blocking': False, 'status': 'diagnostic_pass' if numerical_pass else 'known_diagnostic_failure'}
    if not numerical_pass:
        return {'blocking': True, 'status': 'failed'}
    if kind == 'real' and metrics['scalar_review_required']:
        return {'blocking': True, 'status': 'requires_model_input_review'}
    return {'blocking': True, 'status': 'passed'}

"""
Suggestion engine for MockInterviewEvaluation results.
"""

THRESHOLD = 5.0


def get_suggestions(evaluations):
    """
    Given a queryset or list of MockInterviewEvaluation objects received by a student,
    return a dict with:
        strengths        – list[str]
        weaknesses       – list[str]
        suggestions      – list[str]
        improvement_summary – str
    """
    if not evaluations:
        return {
            'strengths': [],
            'weaknesses': [],
            'suggestions': [],
            'improvement_summary': 'No evaluations received yet.',
            'overall_avg': 0.0,
            'performance_level': 'N/A',
            'avgs': {},
        }

    # Compute averages across all evaluations
    fields = ['communication', 'confidence', 'technical', 'body_language', 'problem_solving']
    totals = {f: 0.0 for f in fields}
    count  = 0

    for ev in evaluations:
        for f in fields:
            totals[f] += float(getattr(ev, f))
        count += 1

    avgs = {f: round(totals[f] / count, 2) for f in fields}

    # Label map
    labels = {
        'communication':   'Communication',
        'confidence':      'Confidence',
        'technical':       'Technical Knowledge',
        'body_language':   'Body Language',
        'problem_solving': 'Problem Solving',
    }

    # Suggestion map
    suggestion_map = {
        'communication':   'Practice HR-style speaking exercises and participate in speaking clubs.',
        'confidence':      'Conduct regular mock rehearsals in front of a mirror or with peers.',
        'technical':       'Revise core subjects and solve previous placement papers.',
        'body_language':   'Work on posture, eye contact, and gesture awareness during practice.',
        'problem_solving': 'Practice aptitude puzzles, case studies, and logical reasoning daily.',
    }

    strengths  = []
    weaknesses = []
    suggestions= []

    for f, avg in avgs.items():
        if avg >= 7.0:
            strengths.append(f"{labels[f]} ({avg}/10)")
        elif avg < THRESHOLD:
            weaknesses.append(f"{labels[f]} ({avg}/10)")
            suggestions.append(suggestion_map[f])

    overall_avg = round(sum(avgs.values()) / len(avgs), 2)

    if overall_avg >= 8:
        level = 'Excellent'
        summary = (f"Outstanding performance with an average of {overall_avg}/10. "
                   "Keep up the great work and mentor your peers!")
    elif overall_avg >= 6:
        level = 'Good'
        summary = (f"Good performance with an average of {overall_avg}/10. "
                   "Focus on addressing the identified weaknesses to reach the top tier.")
    else:
        level = 'Needs Improvement'
        summary = (f"Performance average of {overall_avg}/10 needs improvement. "
                   "Consistent daily practice across all skill areas is strongly recommended.")

    return {
        'strengths':            strengths,
        'weaknesses':           weaknesses,
        'suggestions':          suggestions,
        'improvement_summary':  summary,
        'overall_avg':          overall_avg,
        'performance_level':    level,
        'avgs':                 avgs,
    }

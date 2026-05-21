"""
Pairing algorithm for Mock Interview sessions.

Public API
----------
generate_pairs(session, students) -> list[MockInterviewPair]
    Shuffles `students`, creates even pairs (+ one trio if odd count),
    and avoids repeating pairs seen in the last 3 sessions.
"""

import random
from itertools import combinations

from .models import MockInterviewPair, MockInterviewSession


# ──────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────────

def _recent_pair_sets(exclude_session, n=3):
    """
    Returns a set of frozensets ({id1, id2}) that appeared in the last *n*
    completed/active sessions before `exclude_session`.
    """
    recent_sessions = (
        MockInterviewSession.objects
        .exclude(pk=exclude_session.pk)
        .order_by('-created_at')[:n]
    )
    seen = set()
    for sess in recent_sessions:
        for pair in sess.pairs.all():
            seen.add(frozenset([pair.student1_id, pair.student2_id]))
            if pair.student3_id:
                seen.add(frozenset([pair.student1_id, pair.student3_id]))
                seen.add(frozenset([pair.student2_id, pair.student3_id]))
    return seen


def _build_pairs_from_order(ordered_students):
    """
    Given an ordered list of StudentProfiles, return a list of tuples:
    - (s1, s2, None) for exactly two-student pairs.
    If the count is odd, the last student is paired with the first student 
    (who is already in a pair).
    """
    result = []
    n = len(ordered_students)

    # Create standard pairs
    for i in range(0, n - 1, 2):
        result.append((ordered_students[i], ordered_students[i + 1], None))

    # Handle odd student: pair with someone already paired
    if n % 2 != 0 and n > 1:
        extra = ordered_students[-1]
        # Pair with the first student in the list
        result.append((extra, ordered_students[0], None))

    return result


def _count_conflicts(pair_tuples, seen):
    """Count how many proposed pairs conflict with recently seen pairs."""
    conflicts = 0
    for s1, s2, s3 in pair_tuples:
        if frozenset([s1.pk, s2.pk]) in seen:
            conflicts += 1
        if s3 and frozenset([s1.pk, s3.pk]) in seen:
            conflicts += 1
        if s3 and frozenset([s2.pk, s3.pk]) in seen:
            conflicts += 1
    return conflicts


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

MAX_RETRIES = 20


def generate_pairs(session, students):
    """
    Parameters
    ----------
    session  : MockInterviewSession (already saved)
    students : iterable of StudentProfile objects

    Returns
    -------
    list[MockInterviewPair]  – created database objects
    """
    student_list = list(students)
    if len(student_list) < 2:
        return []

    seen = _recent_pair_sets(session)

    best_order   = None
    best_conflicts = float('inf')

    for _ in range(MAX_RETRIES):
        random.shuffle(student_list)
        proposed = _build_pairs_from_order(student_list)
        c = _count_conflicts(proposed, seen)
        if c == 0:
            best_order = proposed
            break
        if c < best_conflicts:
            best_conflicts = c
            best_order = proposed

    # Persist pairs
    created = []
    for s1, s2, s3 in best_order:
        pair = MockInterviewPair.objects.create(
            session=session,
            student1=s1,
            student2=s2,
            student3=s3,
        )
        created.append(pair)

    return created

"""
resolution.py
─────────────
Propositional Logic Resolution Refutation Engine.

Theory recap (for learners):
  - Resolution is a complete inference rule for propositional logic.
  - To prove that KB ⊨ α (KB entails α), we show KB ∧ ¬α is UNSATISFIABLE.
  - We convert everything to Conjunctive Normal Form (CNF) — a conjunction of
    disjunctive clauses — then apply the resolution rule repeatedly.
  - Resolution rule: from (A ∨ B) and (¬A ∨ C), derive (B ∨ C).
  - If we derive the EMPTY CLAUSE (⊥), the KB+¬α is unsatisfiable → KB ⊨ α. ✓

Literal representation:
  - Positive literal: a plain string, e.g. "P_1_2"  (Pit at row=1, col=2)
  - Negative literal: prefixed with "~",  e.g. "~P_1_2"
  - A clause is a frozenset of literals.
  - The KB is a list of clauses.
"""

from __future__ import annotations
from itertools import combinations
from typing import Optional


# ──────────────────────────────────────────────────────────────────────────────
# Helper utilities
# ──────────────────────────────────────────────────────────────────────────────

def negate(literal: str) -> str:
    """Return the negation of a literal."""
    if literal.startswith("~"):
        return literal[1:]          # double negation → positive
    return "~" + literal


def is_tautology(clause: frozenset) -> bool:
    """
    A clause is a tautology (trivially true) if it contains both a literal
    and its negation, e.g. {P, ~P}.  Tautologies can be safely discarded.
    """
    for lit in clause:
        if negate(lit) in clause:
            return True
    return False


# ──────────────────────────────────────────────────────────────────────────────
# CNF Conversion
# ──────────────────────────────────────────────────────────────────────────────

def biconditional_to_cnf(left: str, right_literals: list[str]) -> list[frozenset]:
    """
    Convert  left ↔ (r1 ∨ r2 ∨ … ∨ rn)  into CNF clauses.

    Biconditional expansion:
        left ↔ (r1 ∨ r2 ∨ … ∨ rn)
      ≡ [left → (r1 ∨ … ∨ rn)] ∧ [(r1 ∨ … ∨ rn) → left]

    Forward direction  (left → disjunction):
        ¬left ∨ r1 ∨ r2 ∨ … ∨ rn   →  one clause

    Backward direction  (each ri → left), i.e. for each ri:
        ¬ri ∨ left                  →  n clauses

    Parameters
    ----------
    left          : the LHS literal (e.g. "B_2_3")
    right_literals: list of literals in the disjunction on the RHS
    """
    clauses: list[frozenset] = []

    # Forward: ¬left ∨ r1 ∨ r2 ∨ …
    forward = frozenset([negate(left)] + right_literals)
    if not is_tautology(forward):
        clauses.append(forward)

    # Backward: for each ri, add (¬ri ∨ left)
    for ri in right_literals:
        backward = frozenset([negate(ri), left])
        if not is_tautology(backward):
            clauses.append(backward)

    return clauses


def unit_clause(literal: str) -> frozenset:
    """Wrap a single literal into a unit clause (a frozenset with one element)."""
    return frozenset([literal])


# ──────────────────────────────────────────────────────────────────────────────
# Resolution Algorithm
# ──────────────────────────────────────────────────────────────────────────────

def resolve(ci: frozenset, cj: frozenset) -> Optional[frozenset]:
    """
    Apply the resolution rule to two clauses.

    For each literal in ci, check if its negation is in cj.
    If yes, produce the resolvent: (ci ∪ cj) − {literal, ¬literal}.
    If the resolvent is a tautology, return None (discard it).

    Returns the resolvent clause, or None if no resolution is possible or
    the result is a tautology.

    Note: We resolve on only ONE complementary pair per call (standard resolution).
    """
    for lit in ci:
        neg_lit = negate(lit)
        if neg_lit in cj:
            # Merge the two clauses and remove the resolved pair
            resolvent = (ci | cj) - {lit, neg_lit}
            if is_tautology(resolvent):
                return None
            return resolvent
    return None   # no complementary pair found


def resolution_entails(kb_clauses: list[frozenset], query_literal: str) -> tuple[bool, int]:
    """
    Decide whether the KB entails `query_literal` using Resolution Refutation.

    Strategy:
      1. Negate the query:  add {¬query_literal} to the clause set.
      2. Repeatedly resolve pairs of clauses to generate new clauses.
      3. If the EMPTY CLAUSE is derived → UNSATISFIABLE → KB ⊨ query.  (True)
      4. If no new clauses can be generated → SATISFIABLE → KB ⊭ query. (False)

    Returns
    -------
    (entailed: bool, steps: int)
        entailed — True if KB entails the query
        steps    — number of resolution steps performed (educational metric)
    """
    # Start with all KB clauses + negation of query
    clauses: list[frozenset] = list(kb_clauses) + [unit_clause(negate(query_literal))]

    # Remove duplicates up front
    clauses = list({c for c in clauses})

    steps = 0

    while True:
        new_clauses: set[frozenset] = set()

        # Try every pair of clauses
        for ci, cj in combinations(clauses, 2):
            resolvent = resolve(ci, cj)
            steps += 1

            if resolvent is not None:
                if len(resolvent) == 0:
                    # Empty clause derived → contradiction → entailed!
                    return True, steps
                new_clauses.add(resolvent)

        # Check if we learned anything new
        new_clauses -= set(clauses)

        if not new_clauses:
            # No new clauses → can't derive contradiction → not entailed
            return False, steps

        clauses.extend(new_clauses)

        # Safety valve: avoid infinite loops in degenerate cases
        if len(clauses) > 2000:
            return False, steps


def is_cell_safe(kb_clauses: list[frozenset], row: int, col: int) -> tuple[bool, int]:
    """
    Ask the KB: is cell (row, col) definitely safe?
    A cell is safe iff ¬P_{row}_{col} AND ¬W_{row}_{col} are both entailed.

    Returns (safe: bool, total_steps: int).
    """
    pit_lit  = f"P_{row}_{col}"
    wump_lit = f"W_{row}_{col}"

    # Prove there's no pit
    no_pit,  s1 = resolution_entails(kb_clauses, f"~{pit_lit}")
    # Prove there's no wumpus
    no_wump, s2 = resolution_entails(kb_clauses, f"~{wump_lit}")

    return (no_pit and no_wump), (s1 + s2)

"""
Model Evaluation module for Banking Customer Support AI Agent.
Evaluates classification accuracy, response quality, and routing success.
"""

import logging
from dataclasses import dataclass, field
from workflow import run_support_agent

logger = logging.getLogger(__name__)


@dataclass
class TestCase:
    user_message: str
    expected_classification: str
    description: str
    customer_name: str = "Test User"


@dataclass
class EvaluationResult:
    test_case: TestCase
    actual_classification: str
    response: str
    routing_correct: bool
    score: float  # 0.0 - 1.0
    notes: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Test suite
# ---------------------------------------------------------------------------

TEST_CASES = [
    TestCase(
        user_message="Thanks for sorting out my net banking login issue.",
        expected_classification="positive_feedback",
        description="Positive feedback - login resolved",
        customer_name="Alice",
    ),
    TestCase(
        user_message="Your service is amazing! The loan approval was so fast.",
        expected_classification="positive_feedback",
        description="Positive feedback - loan approval praise",
        customer_name="Bob",
    ),
    TestCase(
        user_message="My debit card replacement still hasn't arrived after 3 weeks.",
        expected_classification="negative_feedback",
        description="Negative feedback - card delay",
        customer_name="Carol",
    ),
    TestCase(
        user_message="I was charged twice for the same transaction. This is unacceptable.",
        expected_classification="negative_feedback",
        description="Negative feedback - duplicate charge",
        customer_name="David",
    ),
    TestCase(
        user_message="Could you check the status of ticket 650932?",
        expected_classification="query",
        description="Query - ticket status check",
        customer_name="Eve",
    ),
    TestCase(
        user_message="What is the current status of my complaint number 123456?",
        expected_classification="query",
        description="Query - complaint status",
        customer_name="Frank",
    ),
    TestCase(
        user_message="I'm extremely disappointed with the ATM service.",
        expected_classification="negative_feedback",
        description="Negative feedback - ATM complaint",
        customer_name="Grace",
    ),
    TestCase(
        user_message="The mobile app works perfectly now. Great job!",
        expected_classification="positive_feedback",
        description="Positive feedback - mobile app praise",
        customer_name="Henry",
    ),
]


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

EMPATHY_KEYWORDS = ["apologize", "sorry", "understand", "inconvenience", "help", "support", "team"]
POSITIVE_RESPONSE_KEYWORDS = ["thank", "happy", "delight", "appreciate", "assist", "kind"]
QUERY_RESPONSE_KEYWORDS = ["ticket", "marked as", "status", "#"]


def _score_response(response: str, classification: str) -> tuple[float, list[str]]:
    """Score a response on a 0.0-1.0 scale based on content quality."""
    notes = []
    score = 0.5  # Base score for any response

    lower = response.lower()

    if classification == "positive_feedback":
        hits = sum(1 for kw in POSITIVE_RESPONSE_KEYWORDS if kw in lower)
        score = min(1.0, 0.5 + hits * 0.1)
        if hits == 0:
            notes.append("Response lacks warm/appreciative language.")

    elif classification == "negative_feedback":
        hits = sum(1 for kw in EMPATHY_KEYWORDS if kw in lower)
        score = min(1.0, 0.4 + hits * 0.1)
        if "#" in response:
            score = min(1.0, score + 0.2)
            notes.append("Ticket number included in response - good.")
        else:
            notes.append("WARNING: Ticket number missing from negative feedback response.")
        if hits == 0:
            notes.append("Response lacks empathetic language.")

    elif classification == "query":
        hits = sum(1 for kw in QUERY_RESPONSE_KEYWORDS if kw in lower)
        score = min(1.0, 0.5 + hits * 0.15)
        if "marked as" in lower:
            notes.append("Response contains clear ticket status - good.")

    return round(score, 2), notes


# ---------------------------------------------------------------------------
# Evaluation runner
# ---------------------------------------------------------------------------

def run_evaluation(test_cases: list[TestCase] | None = None) -> dict:
    """
    Run evaluation on the provided test cases (defaults to built-in suite).
    Returns a summary dict with per-case results and aggregate metrics.
    """
    cases = test_cases or TEST_CASES
    results: list[EvaluationResult] = []

    print("\n" + "=" * 60)
    print(" MODEL EVALUATION - Banking Support AI Agent")
    print("=" * 60)

    for i, tc in enumerate(cases, 1):
        print(f"\n[{i}/{len(cases)}] {tc.description}")
        print(f"  Message   : {tc.user_message[:70]}")
        print(f"  Expected  : {tc.expected_classification}")

        try:
            state = run_support_agent(tc.user_message, tc.customer_name)
            actual = state["classification"]
            response = state["response"]
            routing_correct = actual == tc.expected_classification
            score, notes = _score_response(response, actual)

            result = EvaluationResult(
                test_case=tc,
                actual_classification=actual,
                response=response,
                routing_correct=routing_correct,
                score=score,
                notes=notes,
            )
            print(f"  Actual    : {actual} {'✓' if routing_correct else '✗'}")
            print(f"  Response  : {response[:100]}...")
            print(f"  Score     : {score}")

        except Exception as exc:
            logger.exception("Error evaluating test case: %s", tc.description)
            result = EvaluationResult(
                test_case=tc,
                actual_classification="error",
                response="",
                routing_correct=False,
                score=0.0,
                notes=[f"Exception: {exc}"],
            )
            print(f"  ERROR     : {exc}")

        results.append(result)

    # Aggregate metrics
    total = len(results)
    routing_correct_count = sum(1 for r in results if r.routing_correct)
    avg_score = sum(r.score for r in results) / total if total else 0.0

    by_class: dict[str, list[float]] = {}
    for r in results:
        by_class.setdefault(r.test_case.expected_classification, []).append(
            1.0 if r.routing_correct else 0.0
        )

    class_accuracy = {cls: sum(v) / len(v) for cls, v in by_class.items()}

    summary = {
        "total_cases": total,
        "routing_success_count": routing_correct_count,
        "routing_success_rate": round(routing_correct_count / total, 2) if total else 0.0,
        "average_response_score": round(avg_score, 2),
        "classification_accuracy": class_accuracy,
        "results": results,
    }

    print("\n" + "=" * 60)
    print(" EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total test cases      : {total}")
    print(f"  Routing success rate  : {summary['routing_success_rate'] * 100:.1f}%  ({routing_correct_count}/{total})")
    print(f"  Avg response score    : {avg_score:.2f} / 1.00")
    print("  Per-class accuracy    :")
    for cls, acc in class_accuracy.items():
        print(f"    {cls:<25}: {acc * 100:.1f}%")
    print("=" * 60)

    return summary


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    run_evaluation()

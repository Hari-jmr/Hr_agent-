import pytest

from backend.services.intent_router import CHAT, POLICY, normalize, route


@pytest.mark.parametrize("text", [
    "hi",
    "Hi",
    "HIIII",
    "hello!",
    "hey there",
    "good morning",
    "GOOD MORNING!!!",
    "good evening.",
    "namaste",
    "gm",
    "yo",
])
def test_greetings_route_to_chat(text):
    assert route(text) == CHAT


@pytest.mark.parametrize("text", [
    "how are you",
    "how r u?",
    "what's up",
    "wassup",
])
def test_how_are_you_routes_to_chat(text):
    assert route(text) == CHAT


@pytest.mark.parametrize("text", [
    "thanks",
    "Thank you!",
    "thx",
    "shukriya",
    "dhanyavaad",
])
def test_thanks_routes_to_chat(text):
    assert route(text) == CHAT


@pytest.mark.parametrize("text", [
    "bye",
    "goodbye",
    "see you soon!",
    "good night",
])
def test_farewell_routes_to_chat(text):
    assert route(text) == CHAT


@pytest.mark.parametrize("text", [
    "who are you",
    "what can you do",
    "help",
    "are you there?",
    "testing",
])
def test_meta_questions_route_to_chat(text):
    assert route(text) == CHAT


@pytest.mark.parametrize("text", [
    "hi, what is the leave policy?",
    "hello! how many annual leaves do I get?",
    "what is the notice period?",
    "and for probation employees?",
    "what about maternity leave in the GMC branch?",
    "I want to claim reimbursement for travel",
])
def test_policy_questions_route_to_policy(text):
    assert route(text) == POLICY


def test_greetings_do_not_trigger_on_longer_messages():
    long_chat = "hi " + ("word " * 20)  # > 60 chars after normalize
    assert route(long_chat) == POLICY


def test_normalize_strips_punctuation_and_case():
    assert normalize("  GooD  Morning!!! ") == "good morning"
    assert normalize("how's it going?") == "how's it going"


def test_empty_routes_to_policy():
    assert route("") == POLICY
    assert route("   ") == POLICY

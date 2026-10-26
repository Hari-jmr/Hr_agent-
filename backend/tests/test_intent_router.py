import json

import pytest

from backend.services.intent_router import (
    CHAT,
    RETRIEVE,
    IntentDecision,
    classify_intent,
    parse_intent_response,
)


@pytest.mark.parametrize(
    ("intent", "reply"),
    [
        (CHAT, "Good to see you!"),
        (RETRIEVE, ""),
    ],
)
def test_parse_valid_classifier_decisions(intent, reply):
    parsed = parse_intent_response(json.dumps({"intent": intent, "reply": reply}))
    assert parsed == IntentDecision(intent, reply)


def test_policy_route_discards_classifier_reply():
    parsed = parse_intent_response(
        json.dumps({"intent": RETRIEVE, "reply": "Unsupported policy claim"})
    )
    assert parsed == IntentDecision(RETRIEVE)


def test_retrieve_route_parses_and_limits_focused_search_queries():
    parsed = parse_intent_response(
        json.dumps(
            {
                "intent": RETRIEVE,
                "reply": "not policy evidence",
                "search_queries": ["leave during notice period", "notice period length"]
                * 4,
            }
        )
    )
    assert parsed.intent == RETRIEVE
    assert parsed.reply == ""
    assert parsed.search_queries == (
        "leave during notice period",
        "notice period length",
        "leave during notice period",
        "notice period length",
    )


def test_non_retrieval_route_without_reply_falls_back_to_retrieval():
    parsed = parse_intent_response(json.dumps({"intent": CHAT, "reply": ""}))
    assert parsed == IntentDecision(RETRIEVE)


@pytest.mark.parametrize(
    "response",
    [
        "not json",
        "[]",
        '{"intent":"unknown","reply":"answer anyway"}',
        '{"intent":null,"reply":""}',
    ],
)
def test_invalid_classifier_output_falls_back_to_retrieval(response):
    assert parse_intent_response(response) == IntentDecision(RETRIEVE)


def test_classifier_reply_is_bounded_and_fenced_json_is_accepted():
    long_reply = "x" * 700
    raw = f"```json\n{json.dumps({'intent': CHAT, 'reply': long_reply})}\n```"
    parsed = parse_intent_response(raw)
    assert parsed.intent == CHAT
    assert len(parsed.reply) == 600


@pytest.mark.asyncio
async def test_classifier_receives_question_and_recent_conversation():
    received = []

    async def fake_classifier(payload):
        received.append(json.loads(payload))
        return json.dumps({"intent": RETRIEVE, "reply": ""})

    history = [
        {"role": "user", "content": "How much leave do I get?"},
        {"role": "assistant", "content": "I found a policy excerpt."},
    ]
    result = await classify_intent(
        "What about during probation?", history, fake_classifier
    )

    assert result == IntentDecision(RETRIEVE)
    assert received == [
        {
            "question": "What about during probation?",
            "recent_conversation": history,
        }
    ]


@pytest.mark.asyncio
async def test_classifier_does_not_use_phrase_rules():
    async def fake_classifier(_payload):
        # Same greeting can be casual or carry a policy question; the model's
        # classification, rather than a hard-coded phrase list, selects the path.
        return json.dumps({"intent": RETRIEVE, "reply": ""})

    result = await classify_intent("hello, how many leave days?", [], fake_classifier)
    assert result.intent == RETRIEVE


@pytest.mark.asyncio
async def test_classifier_failure_falls_back_to_retrieval():
    async def unavailable(_payload):
        raise TimeoutError("classifier unavailable")

    result = await classify_intent("What is the travel policy?", [], unavailable)
    assert result == IntentDecision(RETRIEVE)


@pytest.mark.asyncio
async def test_classifier_uses_chat_lane_for_social_redirect_and_clarification():
    answers = iter(
        [
            json.dumps({"intent": CHAT, "reply": "Nice to chat with you."}),
            json.dumps({"intent": CHAT, "reply": "I handle JMR HR topics."}),
            json.dumps({"intent": CHAT, "reply": "Which process do you mean?"}),
        ]
    )

    async def fake_classifier(_payload):
        return next(answers)

    assert (await classify_intent("hey", [], fake_classifier)).intent == CHAT
    assert (
        await classify_intent("What is the weather?", [], fake_classifier)
    ).intent == CHAT
    assert (
        await classify_intent("What about that?", [], fake_classifier)
    ).intent == CHAT

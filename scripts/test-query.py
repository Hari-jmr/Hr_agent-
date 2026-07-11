#!/usr/bin/env python3
"""
Simple test script for the HR Agent Bot query endpoint.
Sends a question and prints the streaming response.

Usage:
    python scripts/test-query.py "What is my notice period?"
    python scripts/test-query.py --api-url http://localhost:8000 "How many leaves do I get?"
"""

import argparse
import json
import sys

import httpx


def test_query(question: str, api_url: str = "http://localhost:8000"):
    url = f"{api_url}/api/query"
    payload = {
        "question": question,
        "session_id": "test-session-cli"
    }
    
    print(f"🚀 Sending query to {url}")
    print(f"❓ Question: {question}")
    print("-" * 50)
    
    try:
        with httpx.stream("POST", url, json=payload, timeout=60.0) as response:
            if response.status_code != 200:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                return
            
            citations = []
            answer_parts = []
            
            for line in response.iter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                
                msg_type = data.get("type")
                
                if msg_type == "start":
                    citations = data.get("citations", [])
                    if citations:
                        print("📚 Sources found:")
                        for c in citations:
                            print(f"   • {c['document_name']} (p.{c.get('page_number', '?')}) — {c['confidence_score']:.0%} match")
                        print("")
                
                elif msg_type == "chunk":
                    content = data.get("content", "")
                    answer_parts.append(content)
                    print(content, end="", flush=True)
                
                elif msg_type == "end":
                    print("\n" + "-" * 50)
                    print("✅ Response complete")
                    if citations:
                        print(f"📎 {len(citations)} citation(s) attached")
    
    except httpx.ConnectError:
        print(f"❌ Cannot connect to {url}")
        print("   Is the backend running? (cd backend && uvicorn main:app --reload)")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Test HR Agent Bot query endpoint")
    parser.add_argument("question", nargs="?", default="What is my notice period?", help="Question to ask")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Backend API base URL")
    args = parser.parse_args()
    
    test_query(args.question, args.api_url)


if __name__ == "__main__":
    main()

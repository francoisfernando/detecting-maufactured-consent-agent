import asyncio
import json
import os
import sys
from dotenv import load_dotenv

# Ensure we can import app and tests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load credentials early
load_dotenv()

from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.genai import types

from app.agent import app as adk_app
from app.agent import root_agent
from tests.eval.metrics import evaluate

async def run_evaluation():
    dataset_path = os.path.join(os.path.dirname(__file__), "eval/datasets/consent-dataset.json")
    print(f"Loading evaluation dataset from {dataset_path}...")
    
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)
        
    eval_cases = dataset.get("eval_cases", [])
    print(f"Loaded {len(eval_cases)} evaluation cases.")
    
    results = []
    
    # Run each evaluation case
    for index, case in enumerate(eval_cases):
        case_id = case.get("eval_case_id")
        prompt_text = case.get("prompt", {}).get("parts", [{}])[0].get("text", "")
        reference_text = case.get("reference", {}).get("response", {}).get("parts", [{}])[0].get("text", "")
        
        print(f"\n[Case {index + 1}/{len(eval_cases)}] Running inference for: '{case_id}'...")
        
        # Set up a fresh runner for this test case (resets state)
        runner = Runner(
            app=adk_app,
            session_service=InMemorySessionService(),
            artifact_service=InMemoryArtifactService(),
            auto_create_session=True,
        )
        
        user_message = types.Content(
            parts=[types.Part.from_text(text=prompt_text)]
        )
        
        agent_events = []
        try:
            # Run inference with a 180-second timeout
            async def gather_events():
                events = []
                async for event in runner.run_async(
                    user_id="eval_user",
                    session_id=f"eval_session_{case_id}",
                    new_message=user_message
                ):
                    if event.content:
                        events.append(event)
                return events

            print(f"Starting inference with 300s timeout...")
            agent_events = await asyncio.wait_for(gather_events(), timeout=300.0)
            
            # Get final state to retrieve mci_report
            session = await runner.session_service.get_session(
                app_name="app",
                user_id="eval_user",
                session_id=f"eval_session_{case_id}"
            )
            mci_report = session.state.get("mci_report")
            
            # Format output for judge
            final_response = ""
            if mci_report:
                if isinstance(mci_report, dict):
                    final_response = json.dumps(mci_report, indent=2)
                else:
                    final_response = str(mci_report)
            elif agent_events:
                # Fallback to last event content if no structured report
                final_response = agent_events[-1].content
                
            # Construct instance for LLM Judge
            # The metrics.py judge expects: prompt, response, reference, and agent_data
            instance = {
                "prompt": prompt_text,
                "response": final_response,
                "reference": reference_text,
                "agent_data": {"turns": [{"events": [{"author": e.author, "content": e.content} for e in agent_events]}]}
            }
            
            print(f"Grading case: '{case_id}' via LLM-as-judge...")
            verdict = evaluate(instance)
            
            results.append({
                "case_id": case_id,
                "score": verdict.get("score", 0),
                "explanation": verdict.get("explanation", ""),
                "status": "PASS" if verdict.get("score", 0) >= 3 else "FAIL"
            })
            
            print(f"Result: {results[-1]['status']} (Score: {results[-1]['score']}/5)")
            print(f"Reason: {results[-1]['explanation']}")
            
        except asyncio.TimeoutError:
            print(f"Timeout Error: Case '{case_id}' exceeded 300 seconds.")
            results.append({
                "case_id": case_id,
                "score": 0,
                "explanation": "Timeout Error: Execution exceeded 5 minutes",
                "status": "TIMEOUT"
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error executing case '{case_id}': {str(e)}")
            results.append({
                "case_id": case_id,
                "score": 0,
                "explanation": f"Execution Error: {str(e)}",
                "status": "ERROR"
            })
            
    # Print final summary table
    print("\n" + "="*80)
    print(" EVALUATION RESULTS SUMMARY".center(80))
    print("="*80)
    print(f"{'Case ID':<35} | {'Score':<5} | {'Status':<7} | {'Explanation'}")
    print("-"*80)
    for res in results:
        explanation_trunc = res['explanation'][:35] + "..." if len(res['explanation']) > 35 else res['explanation']
        print(f"{res['case_id']:<35} | {res['score']:<5}/5 | {res['status']:<7} | {explanation_trunc}")
    print("="*80)
    
if __name__ == "__main__":
    asyncio.run(run_evaluation())

"""Tests for chain module."""

from promptracer.chain import Chain, ChainStep, ChainResult
from promptracer.prompt import RunResult


def test_chain_step_creation():
    step = ChainStep(template="Hello {{name}}", model="openai/gpt-4o")
    assert step.template == "Hello {{name}}"
    assert step.output_var == "output"


def test_chain_result_empty():
    cr = ChainResult()
    assert cr.final_response == ""
    assert cr.total_cost == 0
    assert cr.total_latency == 0


def test_chain_result_with_steps():
    step = ChainStep(template="test", model="m")
    result = RunResult(
        model="m", response="hello", latency=1.0,
        input_tokens=10, output_tokens=5, cost=0.01, prompt_text="test"
    )
    cr = ChainResult(steps=[(step, result)])
    assert cr.final_response == "hello"
    assert cr.total_cost == 0.01
    assert cr.total_latency == 1.0


def test_chain_builder():
    chain = Chain()
    chain.step("Step 1: {{input}}", model="openai/gpt-4o")
    chain.step("Step 2: {{output}}", model="anthropic/claude-sonnet-4-6")
    assert len(chain._steps) == 2


def test_chain_builder_chaining():
    chain = (
        Chain()
        .step("A: {{x}}")
        .step("B: {{output}}")
        .step("C: {{output}}")
    )
    assert len(chain._steps) == 3


def test_chain_no_steps_raises():
    chain = Chain()
    try:
        chain.run(input="test")
        assert False, "Should have raised"
    except ValueError as e:
        assert "no steps" in str(e)

"""A small independent order Agent used by the consumer repository.

This repository owns the Agent and its test tools. It only imports the released
Agent Regression Kit API; it does not import the kit checkout or copy its core
implementation.
"""

from __future__ import annotations

from typing import Any, Dict

from agent_regression import CallableAgentAdapter, ToolExecutionResult


ORDERS = {
    "123": {
        "order_id": "123",
        "customer_id": "customer-1",
        "status": "not_shipped",
    }
}

BALANCES = {"customer-1": {"customer_id": "customer-1", "balance": 100}}


class OrderTools:
    """The consumer project's deterministic test double for two business tools."""

    def call(self, tool: str, arguments: Dict[str, Any]) -> Any:
        if tool == "get_order":
            order = ORDERS.get(str(arguments.get("order_id")))
            if order is None:
                return ToolExecutionResult(
                    result={"error": "order not found"},
                    is_error=True,
                    error="order not found",
                )
            return dict(order)
        if tool == "get_balance":
            balance = BALANCES.get(str(arguments.get("customer_id")))
            if balance is None:
                return ToolExecutionResult(
                    result={"error": "customer not found"},
                    is_error=True,
                    error="customer not found",
                )
            return dict(balance)
        raise KeyError(f"unknown consumer tool: {tool}")


def build_agent(variant: str = "normal") -> CallableAgentAdapter:
    """Build one normal run or one deliberately injected regression."""

    if variant not in {"normal", "wrong-resource", "skip-tool", "misread-result"}:
        raise ValueError(f"unknown variant: {variant}")

    def run(request: Dict[str, Any], context: Any) -> None:
        order_id = "999" if variant == "wrong-resource" else str(request["order_id"])
        order = context.call_tool("get_order", {"order_id": order_id})
        if variant == "skip-tool":
            context.final_answer(
                "Order status is not shipped; balance was not checked.",
                {"order_status": order.get("status"), "balance_verified": False},
            )
            return

        customer_id = str(order.get("customer_id", "customer-1"))
        balance = context.call_tool("get_balance", {"customer_id": customer_id})
        status = "shipped" if variant == "misread-result" else order.get("status")
        context.final_answer(
            f"Order {order_id} is {status}; balance is {balance.get('balance')}.",
            {"order_status": status, "balance_verified": True},
        )

    return CallableAgentAdapter(
        {"name": "independent-order-agent", "version": "0.1.0", "framework": "consumer-fixture"},
        run,
    )

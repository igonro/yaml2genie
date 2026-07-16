import json
from typing import Final

from yaml2genie.models import DefinitionDocument

COMPLETE_EXAMPLE_SQL: Final = (
    "SELECT SUM(order_amount) FROM sales.analytics.orders WHERE region = :region"
)
COMPLETE_EXAMPLE_JSON: Final = """{
    "version": 2,
    "config": {
        "sample_questions": [
            {
                "id": "00000000000000000000000000000001",
                "question": ["What is revenue?"]
            }
        ]
    },
    "data_sources": {
        "tables": [
            {
                "identifier": "sales.analytics.orders",
                "column_configs": [
                    {
                        "column_name": "order_amount",
                        "display_name": "Order amount",
                        "synonyms": ["revenue", "sales"]
                    }
                ]
            }
        ],
        "metric_views": [
            {
                "identifier": "sales.analytics.revenue_metrics",
                "description": ["Revenue metrics by region."],
                "column_configs": [
                    {
                        "column_name": "period",
                        "display_name": "Reporting period",
                        "description": ["Reporting period."],
                        "synonyms": ["month", "quarter"],
                        "exclude": false,
                        "enable_format_assistance": true,
                        "enable_entity_matching": false
                    }
                ]
            }
        ]
    },
    "instructions": {
        "text_instructions": [
            {
                "id": "00000000000000000000000000000010",
                "content": ["Use fiscal periods."]
            }
        ],
        "example_question_sqls": [
            {
                "id": "00000000000000000000000000000011",
                "question": ["Show sales for a region."],
                "sql": __EXAMPLE_SQL__,
                "parameters": [
                    {
                        "name": "region",
                        "type_hint": "STRING",
                        "description": ["Region to filter."],
                        "default_value": {
                            "values": ["EMEA"]
                        }
                    }
                ],
                "usage_guidance": ["Use for geographic sales questions."]
            }
        ],
        "sql_functions": [
            {
                "id": "00000000000000000000000000000012",
                "identifier": "sales.analytics.fiscal_quarter"
            }
        ],
        "join_specs": [
            {
                "id": "00000000000000000000000000000013",
                "left": {
                    "identifier": "sales.analytics.orders",
                    "alias": "orders"
                },
                "right": {
                    "identifier": "sales.analytics.customers",
                    "alias": "customers"
                },
                "sql": [
                    "`orders`.`customer_id` = `customers`.`customer_id`",
                    "--rt=FROM_RELATIONSHIP_TYPE_MANY_TO_ONE--"
                ],
                "comment": ["Orders belong to customers."],
                "instruction": ["Use when customer attributes are requested."]
            }
        ],
        "sql_snippets": {
            "filters": [
                {
                    "id": "00000000000000000000000000000014",
                    "alias": "high_value",
                    "sql": ["orders.order_amount > 1000"],
                    "display_name": "high value orders",
                    "synonyms": ["large orders", "big purchases"],
                    "comment": ["Filters to large orders."],
                    "instruction": ["Use for high-value requests."]
                }
            ]
        }
    },
    "benchmarks": {
        "questions": [
            {
                "id": "00000000000000000000000000000002",
                "question": ["What is average order value?"],
                "answer": [
                    {
                        "format": "SQL",
                        "content": [
                            "SELECT AVG(order_amount) FROM sales.analytics.orders"
                        ]
                    }
                ]
            }
        ]
    }
}""".replace("__EXAMPLE_SQL__", json.dumps([COMPLETE_EXAMPLE_SQL]))


def complete_example() -> DefinitionDocument:
    return DefinitionDocument.model_validate(json.loads(COMPLETE_EXAMPLE_JSON))

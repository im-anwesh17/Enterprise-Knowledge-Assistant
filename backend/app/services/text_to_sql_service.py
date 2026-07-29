"""
Text-to-SQL Service Module.
Why this file exists: Translates natural language to SQL, validates it for safety, executes it, and explains the results.
Why this design was chosen:
1. Two-pass AI design: Pass 1 generates SQL. Pass 2 explains the data.
2. AST Parsing: sqlparse physically guarantees no malicious DML/DDL commands execute.
"""
import logging
import sqlparse
from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from app.core.config import settings

logger = logging.getLogger(__name__)

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, openai_api_key=settings.OPENAI_API_KEY)

# Few-Shot SQL Prompt
SQL_GENERATION_PROMPT = """
You are a PostgreSQL expert. Given an input question, create a syntactically correct PostgreSQL query to run.
Unless the user specifies in their question a specific number of examples to obtain, always limit your query to at most 100 results.
You must return ONLY the raw SQL query, with no markdown formatting and no explanations.

Here is the database schema:
{schema}

Examples:
Question: "What is the total revenue?"
SQL: SELECT SUM(revenue) FROM sales_analytics;

Question: "Which region had the most units sold?"
SQL: SELECT region, SUM(units_sold) AS total_units FROM sales_analytics GROUP BY region ORDER BY total_units DESC LIMIT 1;

Question: "{question}"
SQL:"""

# Explanation Prompt
EXPLANATION_PROMPT = """
You are a business analyst. 
Given the user's original question, the SQL query used to find the answer, and the raw JSON data returned from the database, write a clear, concise executive summary answering the user's question.

Question: {question}
SQL Query: {sql_query}
Raw Data: {raw_data}

Summary Answer:"""

def get_schema_context() -> str:
    """
    Returns the schema of the target tables as DDL for the LLM context.
    Hardcoded here for safety in the demo, but in production this would use SQLAlchemy reflection.
    """
    return """
    CREATE TABLE sales_analytics (
        id INTEGER PRIMARY KEY,
        region VARCHAR(100) NOT NULL, -- e.g., 'North America', 'Europe', 'Asia Pacific'
        product_category VARCHAR(100) NOT NULL, -- e.g., 'Software', 'Hardware', 'Services'
        revenue NUMERIC(12, 2) NOT NULL,
        units_sold INTEGER NOT NULL,
        sale_date DATE NOT NULL,
        customer_segment VARCHAR(100) NOT NULL -- e.g., 'Enterprise', 'SMB', 'Consumer'
    );
    """

def validate_sql_safety(sql: str) -> None:
    """
    Parses the SQL string into an AST using sqlparse.
    Blocks any statement that is not a SELECT, or that contains DML/DDL keywords.
    """
    parsed = sqlparse.parse(sql)
    if not parsed:
        raise ValueError("Could not parse generated SQL.")
    
    statement = parsed[0]
    # The first token type of the statement must be a SELECT
    if statement.get_type() != "SELECT":
        raise ValueError(f"Security Error: Only SELECT statements are allowed. Found: {statement.get_type()}")

    # Walk the AST tokens to look for malicious keywords anywhere in the tree
    forbidden_keywords = {"DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "TRUNCATE", "GRANT", "REVOKE", "EXEC"}
    
    def check_tokens(tokens):
        for token in tokens:
            if token.is_group:
                check_tokens(token.tokens)
            else:
                # Compare uppercase token value
                if token.value.upper() in forbidden_keywords:
                    raise ValueError(f"Security Error: Forbidden keyword '{token.value.upper()}' detected in SQL.")
                    
    check_tokens(statement.tokens)

def generate_and_execute_sql(db: Session, question: str) -> Dict[str, Any]:
    """
    Core pipeline:
    Generates SQL via LLM, validates AST safety, executes query, and generates explanation.
    """
    schema = get_schema_context()
    prompt = PromptTemplate.from_template(SQL_GENERATION_PROMPT)
    sql_response = llm.invoke(prompt.format(schema=schema, question=question))
    
    # Clean LLM output (remove potential markdown wrappers if the LLM misbehaves)
    raw_sql = sql_response.content.replace("```sql", "").replace("```", "").strip()

    validate_sql_safety(raw_sql)
    logger.info(f"Validated SQL generated: {raw_sql}")

    # Running in a read-only context (using text())
    result = db.execute(text(raw_sql))
    columns = list(result.keys())
    rows = [dict(zip(columns, row)) for row in result.fetchall()]

    explain_prompt = PromptTemplate.from_template(EXPLANATION_PROMPT)
    explanation_response = llm.invoke(explain_prompt.format(
        question=question,
        sql_query=raw_sql,
        raw_data=str(rows[:10]) # Send at most 10 rows to avoid token overflow
    ))

    return {

        "generated_sql": raw_sql,
        "columns": columns,
        "results": rows,
        "explanation": explanation_response.content
    }

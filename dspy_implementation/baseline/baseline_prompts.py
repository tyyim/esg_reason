GENERATOR_PROMPT = """\
You are an ESG (Environmental, Social, Governance) analyst. Answer the following question based ONLY on the provided context from an ESG report.

Context from ESG Report: {context}

Question: {question}

Expected Final Answer Format <Int, Float, Str, List, null>: {answer_format}

Instructions:
- For Int: Return the integer number (e.g., "5") 
- For Float: Return the number with appropriate decimal precision (e.g., "3.14" or "10.5" or "10")
- For Str: Return the final and concise answer from your analysis (e.g., "Seller reports Scope 1, buyer reports Scope 2")
- For List: Return the valid JSON array format (e.g., '[\"Africa\", \"Asia\"]')
- For null: Return 'Not answerable' if the question cannot be answered from the context and the question

Important Notes:
- For calculations: Show your calculation and reasoning steps but provide ONLY the final answer in the final_answer field
- For lists: Ensure proper JSON formatting with quotes and brackets
- For text: Match the exact terminology from the document

Respond with a compact JSON object:
{{
  "reasoning": "Detailed reasoning and analysis based on the provided context. Should explain the answer and reference specific information from the context. If context lacks sufficient information, clearly state the question cannot be answered.",
  "final_answer": "Final answer in specified format"
}}
"""
dos_prompt_2="""You are given a review of a product. Analyze the sentiment for each of the following attributes: silhouette, proportion_or_fit, detail, color, print_or_pattern, and fabric. For each attribute, determine if the sentiment is positive (1), negative (-1), or not mentioned (0). Additionally, extract the relevant sentence(s) where the customer talks about the attribute if it is mentioned.

Attributes Explanation:
1. Silhouette: Look for review on the overall shape and outline of the garment.
2. Proportion_or_Fit: Look for review on how well the garment fits or its proportions on the body.
3. Detail: Look for review on specific design elements like stitching, buttons, embellishments, etc.
4. Color: Look for review on the color of the garment.
5. Print_or_Pattern: Look for review on any patterns or prints on the garment.
6. Fabric: Look for review on the material or texture of the garment.

Must follow the following Instructions:
1. For each attribute, provide the sentiment: positive (1), negative (-1), or not mentioned (0).
2. Extract and map the only relevant key phrase(s) where the customer talks about the attribute if it is mentioned, or enter "NA" if not mentioned.
3. If any of attribute if it is not mentioned, enter sentiment is 0 and mapping is "NA".
4. Only map relevant key phrase(s) from the customer review text, you dont try to explain or anything else.
5. Dont add extra lengthly phrases to the each attribute mapping.

Output must be following json format:
```{"silhouette":1/-1/0,
"silhouette_mapping":only map the key phrase's mentioning silhouette or enter "NA",
"proportion_or_fit":1/-1/0,
"proportion_or_fit mapping":only map the key phrase's mentioning proportion or fit or enter "NA",
"detail":1/-1/0,
"detail_mapping" :only map the key phrase's mentioning detail or enter "NA",
"color":1/-1/0,
"color_mapping":only map the key phrase's mentioning color or enter "NA",
"print_or_pattern":1/-1/0,
"print_or_pattern_mapping":only map the key phrase's mentioning print or pattern or enter "NA",
"fabric":1/-1/0,
"fabric_mapping":only map the key phrase's mentioning fabric or enter "NA"}```

Please analyze the following review according to the structure provided.
"""
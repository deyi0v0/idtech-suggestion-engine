# TODO: Define these Pydantic models:
# - MerchantInput: industry, location, environment, payment_methods (list[str]), transaction_volume, connectivity_preference (optional), budget (optional)
# - ProductResponse: id, name, category, environment, payment_methods (list[str]), price, description
# - RecommendationResponse: recommendations (list[ProductResponse]), explanation (str)
# - CompatibilityRequest: product_ids (list[int])
# - CompatibilityResponse: compatible (bool), issues (list[str])
# - ComparisonResponse: products (list[ProductResponse])
# - ChatMessage: role (str), content (str)
# - ChatRequest: message (str), history (list[ChatMessage]), merchant_context (MerchantInput | None)
# - ChatResponse: reply (str), recommendations (list[ProductResponse] | None)

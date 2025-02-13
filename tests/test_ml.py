from data_pipeline.ml.fraud_detection import predict_fraud

def test_fraud_detection():
    fraud_result = predict_fraud()
    assert "fraud_score" in fraud_result, "Fraud score missing in response"
    assert fraud_result["fraud_score"] >= 0, "Fraud score should not be negative"

test_fraud_detection()
print("✅ ML fraud detection test passed.")


def test_detect_breaking_changes():
    from archguard.contract_checker import detect_breaking_changes

    old_schema = {
        "paths": {
            "/api/charge": {
                "post": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "transaction_id": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    new_schema = {
        "paths": {
            "/api/charge": {
                "post": {
                    "responses": {
                        "200": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "properties": {
                                            "txn": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    diff = detect_breaking_changes(old_schema, new_schema)
    assert diff is not None
    assert "Property 'transaction_id' removed" in diff

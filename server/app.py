from flask import Flask, request, jsonify
from db import *
from crypto_eval import compute_encrypted_similarity

app = Flask(__name__)
init_db()

@app.post("/setup")
def setup():
    data = request.get_json()

    user_id = data.get("user_id")
    key_id = data.get("key_id")
    eval_mult_key = data.get("eval_mult_key")
    eval_sum_key = data.get("eval_sum_key")

    if not user_id or not key_id or not eval_mult_key or not eval_sum_key:
        return jsonify({
            "error": "user_id, key_id, eval_mult_key, eval_sum_key are required"
        }), 400

    save_eval_keys(key_id, user_id, eval_mult_key, eval_sum_key)

    return jsonify({
        "status": "setup_done",
        "user_id": user_id,
        "key_id": key_id
    })


@app.post("/register")
def register():
    data = request.get_json()

    user_id = data.get("user_id")
    key_id = data.get("key_id")
    enc_emb = data.get("encrypted_embedding")

    if not user_id or not key_id or not enc_emb:
        return jsonify({
            "error": "user_id, key_id, encrypted_embedding are required"
        }), 400

    save_ciphertext(user_id, key_id, enc_emb)

    return jsonify({
        "status": "registered",
        "user_id": user_id,
        "key_id": key_id
    })


@app.post("/verify")
def verify():
    data = request.get_json()

    user_id = data.get("user_id")
    key_id = data.get("key_id")
    enc_query = data.get("encrypted_embedding")

    if not user_id or not key_id or not enc_query:
        return jsonify({
            "error": "user_id, key_id, encrypted_embedding are required"
        }), 400

    template = load_ciphertext(user_id)

    if template is None:
        return jsonify({"error": "user_id not registered"}), 404

    template_key_id = template["key_id"]
    enc_template = template["encrypted_embedding"]

    if template_key_id != key_id:
        return jsonify({
            "error": "key_id mismatch",
            "template_key_id": template_key_id,
            "request_key_id": key_id
        }), 400

    eval_keys = load_eval_keys(key_id)

    if eval_keys is None:
        return jsonify({"error": "eval keys not setup"}), 404

    enc_similarity, ckks_time = compute_encrypted_similarity(
        enc_template,
        enc_query,
        eval_keys["eval_mult_key"],
        eval_keys["eval_sum_key"],
    )

    return jsonify({
        "user_id": user_id,
        "key_id": key_id,
        "encrypted_similarity": enc_similarity,
        "time" : ckks_time
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
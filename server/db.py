import sqlite3

DB_PATH = "ciphertext.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS face_embeddings (
            user_id TEXT PRIMARY KEY,
            key_id TEXT NOT NULL,
            encrypted_embedding TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_keys (
            key_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            eval_mult_key TEXT NOT NULL,
            eval_sum_key TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def save_eval_keys(key_id, user_id, eval_mult_key, eval_sum_key):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO user_keys (key_id, user_id, eval_mult_key, eval_sum_key, updated_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(key_id)
        DO UPDATE SET
            user_id = excluded.user_id,
            eval_mult_key = excluded.eval_mult_key,
            eval_sum_key = excluded.eval_sum_key,
            updated_at = CURRENT_TIMESTAMP
    """, (key_id, user_id, eval_mult_key, eval_sum_key))

    conn.commit()
    conn.close()


def load_eval_keys(key_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT eval_mult_key, eval_sum_key
        FROM user_keys
        WHERE key_id = ?
    """, (key_id,))

    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "eval_mult_key": row[0],
        "eval_sum_key": row[1]
    }


def save_ciphertext(user_id, key_id, encrypted_embedding):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO face_embeddings (user_id, key_id, encrypted_embedding, updated_at)
        VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id)
        DO UPDATE SET
            key_id = excluded.key_id,
            encrypted_embedding = excluded.encrypted_embedding,
            updated_at = CURRENT_TIMESTAMP
    """, (user_id, key_id, encrypted_embedding))

    conn.commit()
    conn.close()


def load_ciphertext(user_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT key_id, encrypted_embedding
        FROM face_embeddings
        WHERE user_id = ?
    """, (user_id,))

    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    return {
        "key_id": row[0],
        "encrypted_embedding": row[1]
    }




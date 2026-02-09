import sqlite3
import zlib

DB_NAME = "vyom_knowledge_compressed.db"

def read_data():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    topic_name = input("Enter Topic Name to Read (or type 'random'): ")
    
    if topic_name == 'random':
        cursor.execute("SELECT topic, compressed_content FROM knowledge ORDER BY RANDOM() LIMIT 1")
    else:
        cursor.execute("SELECT topic, compressed_content FROM knowledge WHERE topic LIKE ?", (f"%{topic_name}%",))
        
    row = cursor.fetchone()
    
    if row:
        topic, blob = row
        # Decompressing (वापस टेक्स्ट बनाना)
        original_text = zlib.decompress(blob).decode("utf-8")
        
        print("\n" + "="*50)
        print(f"📖 READING TOPIC: {topic}")
        print("="*50 + "\n")
        print(original_text)
    else:
        print("❌ Topic not found!")

    conn.close()

if __name__ == "__main__":
    read_data()
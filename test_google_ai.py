import google.generativeai as genai

key = "AIzaSyCepW7gkzB-ETNAxlsEg7_HwLNU7UTlRlI"
genai.configure(api_key=key)

print(f"Testing key: {key}")
try:
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content("Hi", generation_config={"max_output_tokens": 5})
    print(f"✅ Success! Response: {response.text}")
except Exception as e:
    print(f"❌ Failed: {e}")

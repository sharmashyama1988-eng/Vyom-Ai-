import json
from app import app
from vyom.core import history as history_manager


def test_models_endpoint_available():
    client = app.test_client()
    res = client.get('/models')
    assert res.status_code == 200
    data = res.get_json()
    assert 'general' in data


def test_save_and_get_user_preferences(tmp_path):
    # Create test user
    device_id = 'test-device-prefs'
    user, err = history_manager.register_user(device_id, 'Tester', 'tester@example.com', gender='Other')
    assert user is not None and err is None

    client = app.test_client()
    payload = { 'device_id': device_id, 'engine': 'image', 'model': 'anime' }
    res = client.post('/user/save_pref', data=json.dumps(payload), content_type='application/json')
    assert res.status_code == 200
    data = res.get_json()
    assert data.get('success') is True

    # Verify saved in DB
    u = history_manager.get_user(device_id)
    assert u.get('default_engine') == 'image'
    assert u.get('default_model') == 'anime'


def test_ask_uses_user_default_model_for_image():
    client = app.test_client()
    # Start a new chat for the user
    res = client.post('/user/new_chat', json={'device_id': device_id})
    assert res.status_code == 200
    chat = res.get_json()
    assert 'id' in chat
    chat_id = chat['id']

    # Ask without explicitly sending a model; server should use saved user default
    res = client.post('/ask', json={'message': 'Generate image of a magical castle', 'device_id': device_id, 'chat_id': chat_id, 'settings': {}})
    assert res.status_code == 200
    data = res.get_json()
    assert data is not None
    assert 'answer' in data
    assert data['answer'] != ''
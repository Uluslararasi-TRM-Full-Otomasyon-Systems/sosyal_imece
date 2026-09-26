import app

client = app.app.test_client()
resp = client.get('/health')
print('APP_IMPORT_OK')
print('ROUTE_COUNT', len(list(app.app.url_map.iter_rules())))
print('HEALTH_STATUS', resp.status_code, resp.get_json())

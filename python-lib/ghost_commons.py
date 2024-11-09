def get_api_token_from_config(config):
    # config={'preset_type': 'service_account', 
    # 'service_account': {'ghost_instance_url': 'http://lemonde.fr', 'api_key': '1234'}, 'user_account': {}}
    preset_type = config.get("preset_type", "service_account")
    account = config.get(preset_type, {})
    api_key = account.get("api_key")
    return api_key


def get_instance_url_from_config(config):
    preset_type = config.get("preset_type", "service_account")
    account = config.get(preset_type, {})
    ghost_instance_url = account.get("ghost_instance_url", "")
    ghost_instance_url = ghost_instance_url.strip("/")
    return ghost_instance_url


def get_id_and_secret(api_key):
    key_segments = api_key.split(':')
    if len(key_segments) != 2:
        raise Exception("This is not a valid admin API key")
    return key_segments[0], key_segments[1]

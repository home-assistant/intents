def merge_dict(base_dict, new_dict):
    for key, value in new_dict.items():
        if key in base_dict:
            old_value = base_dict[key]
            if isinstance(old_value, dict):
                assert isinstance(value, dict), f"Not a dict: {value}"
                merge_dict(old_value, value)
            elif isinstance(old_value, list):
                assert isinstance(value, list), f"Not a list: {value}"
                old_value.extend(value)
            else:
                # Overwrite
                base_dict[key] = value
        else:
            base_dict[key] = value

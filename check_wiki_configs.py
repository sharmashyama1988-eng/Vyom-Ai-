from datasets import get_dataset_config_names # type: ignore

try:
    print("Fetching Wikipedia configs...")
    configs = get_dataset_config_names("wikipedia")
    en_configs = [c for c in configs if ".en" in c]
    print(f"Total English configs: {len(en_configs)}")
    print("Top 10 available versions:")
    for c in en_configs[:10]:
        print(f" - {c}")
except Exception as e:
    print(f"Error: {e}")

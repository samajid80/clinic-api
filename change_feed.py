import time
from cosmos_client import get_container

def watch_changes():
    container = get_container()
    print("Watching for changes... insert a document in the portal.")
    
    continuation_token = None
    
    while True:
        feed = container.query_items_change_feed(
            is_start_from_beginning=True,
            continuation=continuation_token
        )
        
        for change in feed:
            print(f"CHANGE DETECTED:")
            print(f"  Patient: {change.get('name', 'unknown')}")
            print(f"  City:    {change.get('city', 'unknown')}")
            print(f"  Action:  insert or update")
            print("---")
        
        time.sleep(3)

if __name__ == "__main__":
    watch_changes()
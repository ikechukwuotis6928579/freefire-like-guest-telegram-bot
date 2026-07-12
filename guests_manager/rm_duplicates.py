import json
import os

def remove_duplicates_from_formatted(file_path, backup=True):
    """Remove duplicates from formatted_guests.json (guest key format)"""
    try:
        # Create backup if requested
        if backup and os.path.exists(file_path):
            backup_path = file_path.replace('.json', '_backup.json')
            with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())
            print(f"Backup created: {backup_path}")

        # Load the formatted data
        with open(file_path, 'r') as f:
            data = json.load(f)

        seen_uids = set()
        cleaned_data = {}
        duplicates_removed = 0
        guest_counter = 1

        # Process each guest, keeping only first occurrence of each UID
        for guest_key in sorted(data.keys()):
            guest_info = data[guest_key]
            uid = guest_info.get("uid")
            
            # Skip invalid entries
            if not uid or uid == "unknown_uid":
                continue
            
            # If UID not seen before, keep it
            if uid not in seen_uids:
                seen_uids.add(uid)
                new_key = f"guest{guest_counter}"
                cleaned_data[new_key] = guest_info
                guest_counter += 1
            else:
                duplicates_removed += 1

        # Save cleaned data
        with open(file_path, 'w') as f:
            json.dump(cleaned_data, f, indent=2)

        print(f"Formatted file cleanup complete:")
        print(f"  - Original entries: {len(data)}")
        print(f"  - Duplicates removed: {duplicates_removed}")
        print(f"  - Remaining entries: {len(cleaned_data)}")

        return len(data), duplicates_removed, len(cleaned_data)

    except Exception as e:
        print(f"Error processing formatted file: {e}")
        return 0, 0, 0

def remove_duplicates_from_converted(file_path, backup=True):
    """Remove duplicates from guests_converted.json (list format)"""
    try:
        # Create backup if requested
        if backup and os.path.exists(file_path):
            backup_path = file_path.replace('.json', '_backup.json')
            with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())
            print(f"Backup created: {backup_path}")

        # Load the list data
        with open(file_path, 'r') as f:
            data = json.load(f)

        seen_uids = set()
        cleaned_data = []
        duplicates_removed = 0

        # Process each guest in the list
        for guest in data:
            uid = guest.get("uid")
            
            # Skip invalid entries
            if not uid or uid == "unknown_uid":
                continue
            
            # If UID not seen before, keep it
            if uid not in seen_uids:
                seen_uids.add(uid)
                cleaned_data.append(guest)
            else:
                duplicates_removed += 1

        # Save cleaned data
        with open(file_path, 'w') as f:
            json.dump(cleaned_data, f, indent=4)

        print(f"Converted file cleanup complete:")
        print(f"  - Original entries: {len(data)}")
        print(f"  - Duplicates removed: {duplicates_removed}")
        print(f"  - Remaining entries: {len(cleaned_data)}")

        return len(data), duplicates_removed, len(cleaned_data)

    except Exception as e:
        print(f"Error processing converted file: {e}")
        return 0, 0, 0

def remove_all_duplicates(formatted_file="formatted_guests.json", 
                         converted_file="guests_converted.json", 
                         create_backup=True):
    """Remove duplicates from both files"""
    print("=" * 60)
    print("DUPLICATE REMOVAL TOOL")
    print("=" * 60)
    
    total_original = 0
    total_duplicates = 0
    total_remaining = 0
    
    # Process formatted file
    if os.path.exists(formatted_file):
        print(f"\nProcessing: {formatted_file}")
        orig, dupes, remaining = remove_duplicates_from_formatted(formatted_file, create_backup)
        total_original += orig
        total_duplicates += dupes
        total_remaining += remaining
    else:
        print(f"File not found: {formatted_file}")
    
    print("\n" + "-" * 40)
    
    # Process converted file
    if os.path.exists(converted_file):
        print(f"\nProcessing: {converted_file}")
        orig, dupes, remaining = remove_duplicates_from_converted(converted_file, create_backup)
        total_original += orig
        total_duplicates += dupes
        total_remaining += remaining
    else:
        print(f"File not found: {converted_file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total original entries: {total_original}")
    print(f"Total duplicates removed: {total_duplicates}")
    print(f"Total remaining entries: {total_remaining}")
    
    if create_backup:
        print("\nBackup files created with '_backup' suffix")
    
    print("Duplicate removal complete!")

# Additional utility function for advanced duplicate detection
def find_duplicates_report(formatted_file="formatted_guests.json", 
                          converted_file="guests_converted.json"):
    """Generate a report of duplicates without removing them"""
    print("DUPLICATE DETECTION REPORT")
    print("=" * 40)
    
    all_uids = {}  # uid -> [file, key/index, full_info]
    
    # Check formatted file
    if os.path.exists(formatted_file):
        with open(formatted_file, 'r') as f:
            data = json.load(f)
        
        for key, guest_info in data.items():
            uid = guest_info.get("uid")
            if uid and uid != "unknown_uid":
                if uid in all_uids:
                    all_uids[uid].append([formatted_file, key, guest_info])
                else:
                    all_uids[uid] = [[formatted_file, key, guest_info]]
    
    # Check converted file
    if os.path.exists(converted_file):
        with open(converted_file, 'r') as f:
            data = json.load(f)
        
        for i, guest_info in enumerate(data):
            uid = guest_info.get("uid")
            if uid and uid != "unknown_uid":
                if uid in all_uids:
                    all_uids[uid].append([converted_file, f"index_{i}", guest_info])
                else:
                    all_uids[uid] = [[converted_file, f"index_{i}", guest_info]]
    
    # Find and report duplicates
    duplicates_found = False
    for uid, occurrences in all_uids.items():
        if len(occurrences) > 1:
            duplicates_found = True
            print(f"\nDuplicate UID: {uid}")
            for file_name, location, info in occurrences:
                print(f"  - File: {file_name}, Location: {location}")
    
    if not duplicates_found:
        print("No duplicates found!")

if __name__ == "__main__":
    # Choose what you want to do:
    
    # Option 1: Remove duplicates from both files (with backup)
    remove_all_duplicates()
    
    # Option 2: Just generate a report without removing (uncomment to use)
    # find_duplicates_report()
    
    # Option 3: Remove duplicates without creating backup (uncomment to use)  
    # remove_all_duplicates(create_backup=False)

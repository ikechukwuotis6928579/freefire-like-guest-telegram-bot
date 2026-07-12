# Protective Source License v1.0 (PSL-1.0)
# Copyright (c) 2025 Kaif
# Unauthorized removal of credits or use for abusive/illegal purposes
# will terminate all rights granted under this license.

import json
import os

def format_and_convert_guest_data(input_file_path, formatted_output_file, converted_output_file):
    try:
        # Load the raw guest data from input file
        with open(input_file_path, 'r') as f:
            guest_list = json.load(f)

        # Load existing formatted data if output file exists, else start fresh
        if os.path.exists(formatted_output_file):
            with open(formatted_output_file, 'r') as f:
                formatted_data = json.load(f)
        else:
            formatted_data = {}

        # Get existing UIDs to check for duplicates
        existing_uids = set()
        for guest_info in formatted_data.values():
            uid = guest_info.get("uid")
            if uid and uid != "unknown_uid":
                existing_uids.add(uid)

        # Find the next guest number to avoid overwriting keys
        existing_numbers = [
            int(key.replace("guest", ""))
            for key in formatted_data.keys()
            if key.startswith("guest") and key[5:].isdigit()
        ]
        next_number = max(existing_numbers) + 1 if existing_numbers else 1

        # Process new guests and skip duplicates
        new_guests_added = 0
        skipped_duplicates = 0
        skipped_invalid = 0
        
        for guest in guest_list:
            uid = guest.get("uid")
            password = guest.get("password")
            
            # Skip if UID or password is unknown/invalid
            if uid == "unknown_uid" or password == "unknown_password" or not uid or not password:
                skipped_invalid += 1
                continue
            
            # Skip if UID already exists
            if uid in existing_uids:
                skipped_duplicates += 1
                continue
            
            # Add new guest
            guest_key = f"guest{next_number + new_guests_added}"
            
            formatted_guest = {
                "uid": uid,
                "pass": password
            }
            
            formatted_data[guest_key] = formatted_guest
            existing_uids.add(uid)  # Add to set to prevent duplicates within the same batch
            new_guests_added += 1

        # Save formatted data
        with open(formatted_output_file, 'w') as f:
            json.dump(formatted_data, f, indent=2)

        # Convert to pretty format (clean list)
        converted_list = []
        for guest_info in formatted_data.values():
            uid = guest_info.get("uid", "")
            passwd = guest_info.get("pass", "")
            if uid and passwd and uid != "unknown_uid" and passwd != "unknown_password":
                converted_list.append({
                    "uid": uid,
                    "password": passwd
                })

        # Save converted data
        with open(converted_output_file, 'w') as f:
            json.dump(converted_list, f, indent=4)

        # Print summary
        print(f"Processing complete:")
        print(f"  - Added {new_guests_added} new guests")
        print(f"  - Skipped {skipped_duplicates} duplicate guests")
        print(f"  - Skipped {skipped_invalid} invalid guests")
        print(f"  - Total guests in database: {len(formatted_data)}")
        print(f"  - Formatted data saved to: {formatted_output_file}")
        print(f"  - Converted data saved to: {converted_output_file}")

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_file_path}")
        print(f"\nMake sure you used frida hooks and saved the guests runtime")
    except json.JSONDecodeError as e:
        print(f"Error: Could not decode JSON. Check formatting. Details: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    input_file = "/storage/emulated/0/Android/media/com.dts.freefiremax/guest_accounts.json"
    formatted_output_file = "formatted_guests.json"
    converted_output_file = "guests_converted.json"

    format_and_convert_guest_data(input_file, formatted_output_file, converted_output_file)

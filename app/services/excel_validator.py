import re
from typing import List, Dict, Any
from app.constants.hackathon_rules import HACKATHON_RULES

class ExcelValidator:
    @staticmethod
    def validate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        errors = []
        warnings = []
        valid_rows_count = 0
        
        seen_roll_numbers = {}
        seen_emails = {}
        seen_mobiles = {}
        
        teams = {}
        
        # Header mappings to internal names for easier validation
        header_map = {
            "s.no": "s_no",
            "roll number": "roll_number",
            "full name": "full_name",
            "current year": "current_year",
            "branch": "branch",
            "college name": "college_name",
            "gmail address": "email",
            "mobile number": "mobile_number",
            "select domain (drop down)": "domain",
            "mode (drop down)": "mode",
            "team name": "team_name"
        }
        
        # Reverse map to get original column name for error reporting
        def get_orig_col(col_key: str, row: dict) -> str:
            for k in row.keys():
                if k.lower().strip() == col_key:
                    return k
            return col_key

        if not rows:
            return {
                "success": False,
                "status": "validation_failed",
                "summary": {"total_rows": 0, "valid_rows": 0, "invalid_rows": 0, "warnings": 0},
                "errors": [{"row": 0, "field": "File", "value": "", "code": "EMPTY_FILE", "message": "File contains no data rows."}],
                "warnings": []
            }
            
        # Validate headers based on the first row
        first_row_keys = [k.lower().strip() for k in rows[0].keys()]
        required_keys = ["roll number", "full name", "current year", "branch", "college name", "gmail address", "mobile number", "select domain (drop down)", "mode (drop down)"]
        missing_keys = [k for k in required_keys if k not in first_row_keys]
        if missing_keys:
            return {
                "success": False,
                "status": "validation_failed",
                "summary": {"total_rows": len(rows), "valid_rows": 0, "invalid_rows": len(rows), "warnings": 0},
                "errors": [{"row": 1, "field": "Headers", "value": ", ".join(missing_keys), "code": "MISSING_HEADERS", "message": f"Missing required columns: {', '.join(missing_keys)}"}],
                "warnings": []
            }

        normalized_rows = []

        for i, row in enumerate(rows):
            row_num = i + 2  # Excel row number (1-indexed header, data starts at 2)
            row_errors = []
            
            # Create a normalized row dict for easier access
            norm_row = {}
            for k, v in row.items():
                mapped_key = header_map.get(k.lower().strip(), k)
                norm_row[mapped_key] = str(v).strip()
                
            # 1. Roll Number Validation
            roll = norm_row.get("roll_number", "")
            orig_roll_col = get_orig_col("roll number", row)
            if not roll:
                row_errors.append({"row": row_num, "field": orig_roll_col, "value": roll, "code": "REQUIRED_FIELD", "message": "Roll Number is required."})
            elif not re.match(r"^[A-Za-z0-9]+$", roll):
                row_errors.append({"row": row_num, "field": orig_roll_col, "value": roll, "code": "INVALID_FORMAT", "message": "Roll Number must contain only letters and numbers."})
            else:
                roll = roll.upper()
                norm_row["roll_number"] = roll
                if roll in seen_roll_numbers:
                    seen_roll_numbers[roll].append(row_num)
                else:
                    seen_roll_numbers[roll] = [row_num]

            # 2. Full Name Validation
            name = norm_row.get("full_name", "")
            orig_name_col = get_orig_col("full name", row)
            if not name:
                row_errors.append({"row": row_num, "field": orig_name_col, "value": name, "code": "REQUIRED_FIELD", "message": "Full Name is required."})
            elif not re.match(r"^[A-Za-z\s]+$", name):
                row_errors.append({"row": row_num, "field": orig_name_col, "value": name, "code": "INVALID_FORMAT", "message": "Student Name must contain letters and spaces only."})

            # 3. Current Year Validation
            year = norm_row.get("current_year", "")
            orig_year_col = get_orig_col("current year", row)
            if not year:
                row_errors.append({"row": row_num, "field": orig_year_col, "value": year, "code": "REQUIRED_FIELD", "message": "Current Year is required."})
            elif year not in HACKATHON_RULES["allowed_years"]:
                row_errors.append({"row": row_num, "field": orig_year_col, "value": year, "code": "INVALID_VALUE", "message": f"Allowed values: {', '.join(HACKATHON_RULES['allowed_years'])}"})

            # 4. Branch & College Name
            branch = norm_row.get("branch", "")
            if not branch:
                row_errors.append({"row": row_num, "field": get_orig_col("branch", row), "value": branch, "code": "REQUIRED_FIELD", "message": "Branch is required."})
            else:
                norm_row["branch"] = branch.upper()
                
            college = norm_row.get("college_name", "")
            if not college:
                row_errors.append({"row": row_num, "field": get_orig_col("college name", row), "value": college, "code": "REQUIRED_FIELD", "message": "College Name is required."})

            # 5. Email Validation
            email = norm_row.get("email", "")
            orig_email_col = get_orig_col("gmail address", row)
            if not email:
                row_errors.append({"row": row_num, "field": orig_email_col, "value": email, "code": "REQUIRED_FIELD", "message": "Email is required."})
            elif not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
                row_errors.append({"row": row_num, "field": orig_email_col, "value": email, "code": "INVALID_FORMAT", "message": "Invalid email format."})
            else:
                email = email.lower()
                norm_row["email"] = email
                if email in seen_emails:
                    seen_emails[email].append(row_num)
                else:
                    seen_emails[email] = [row_num]

            # 6. Mobile Validation
            mobile = norm_row.get("mobile_number", "")
            if mobile.endswith(".0"):
                mobile = mobile[:-2] # Handle float parsed as string
            orig_mobile_col = get_orig_col("mobile number", row)
            
            if not mobile:
                row_errors.append({"row": row_num, "field": orig_mobile_col, "value": mobile, "code": "REQUIRED_FIELD", "message": "Mobile Number is required."})
            elif not re.match(r"^\d{10}$", mobile):
                row_errors.append({"row": row_num, "field": orig_mobile_col, "value": mobile, "code": "INVALID_FORMAT", "message": "Mobile Number must be exactly 10 digits."})
            else:
                norm_row["mobile_number"] = mobile
                if mobile in seen_mobiles:
                    seen_mobiles[mobile].append(row_num)
                else:
                    seen_mobiles[mobile] = [row_num]

            # 7. Domain Validation
            domain = norm_row.get("domain", "")
            orig_domain_col = get_orig_col("select domain (drop down)", row)
            if not domain:
                row_errors.append({"row": row_num, "field": orig_domain_col, "value": domain, "code": "REQUIRED_FIELD", "message": "Domain is required."})
            else:
                # Case-insensitive match for allowed domains
                matched_domain = next((d for d in HACKATHON_RULES["allowed_domains"] if d.lower() == domain.lower()), None)
                if not matched_domain:
                    row_errors.append({"row": row_num, "field": orig_domain_col, "value": domain, "code": "INVALID_VALUE", "message": "Invalid Domain selected."})
                else:
                    norm_row["domain"] = matched_domain

            # 8. Mode & Team Validation
            mode = norm_row.get("mode", "")
            orig_mode_col = get_orig_col("mode (drop down)", row)
            team_name = norm_row.get("team_name", "")
            orig_team_col = get_orig_col("team name", row)
            
            matched_mode = next((m for m in HACKATHON_RULES["allowed_modes"] if m.lower() == mode.lower()), None)
            
            if not mode:
                row_errors.append({"row": row_num, "field": orig_mode_col, "value": mode, "code": "REQUIRED_FIELD", "message": "Mode is required."})
            elif not matched_mode:
                row_errors.append({"row": row_num, "field": orig_mode_col, "value": mode, "code": "INVALID_VALUE", "message": "Mode must be Individual or Team."})
            else:
                norm_row["mode"] = matched_mode
                if matched_mode == "Individual":
                    if team_name:
                        row_errors.append({"row": row_num, "field": orig_team_col, "value": team_name, "code": "INVALID_STATE", "message": "Team Name must be empty when Mode is Individual."})
                elif matched_mode == "Team":
                    if not team_name:
                        row_errors.append({"row": row_num, "field": orig_team_col, "value": team_name, "code": "REQUIRED_FIELD", "message": "Team Name is required when Mode is Team."})
                    else:
                        norm_row["team_name"] = team_name
                        if team_name not in teams:
                            teams[team_name] = {"members": [], "domain": norm_row.get("domain", "")}
                        teams[team_name]["members"].append(row_num)
                        
                        # Validate team domain consistency
                        if norm_row.get("domain") and teams[team_name]["domain"] and teams[team_name]["domain"] != norm_row.get("domain"):
                            row_errors.append({"row": row_num, "field": orig_domain_col, "value": domain, "code": "TEAM_INCONSISTENCY", "message": f"Team members must have the same domain. Team '{team_name}' has mixed domains."})
                            
            if not row_errors:
                valid_rows_count += 1
            else:
                errors.extend(row_errors)
                
            normalized_rows.append(norm_row)

        # Post-process Duplicates
        for roll, rows_list in seen_roll_numbers.items():
            if len(rows_list) > 1:
                for r in rows_list:
                    # if the row already failed for Roll Number, don't duplicate error
                    if not any(e["row"] == r and e["code"] in ("REQUIRED_FIELD", "INVALID_FORMAT") and "Roll Number" in e["message"] for e in errors):
                        errors.append({"row": r, "field": "Roll Number", "value": roll, "code": "DUPLICATE_ROLL_NUMBER", "message": f"Roll Number appears {len(rows_list)} times in this file."})

        for email, rows_list in seen_emails.items():
            if len(rows_list) > 1:
                for r in rows_list:
                    if not any(e["row"] == r and "Email" in e["message"] for e in errors):
                        errors.append({"row": r, "field": "Gmail Address", "value": email, "code": "DUPLICATE_EMAIL", "message": f"Email appears {len(rows_list)} times in this file."})
                        
        for mobile, rows_list in seen_mobiles.items():
            if len(rows_list) > 1:
                for r in rows_list:
                    if not any(e["row"] == r and "Mobile Number" in e["message"] for e in errors):
                        errors.append({"row": r, "field": "Mobile Number", "value": mobile, "code": "DUPLICATE_MOBILE", "message": f"Mobile Number appears {len(rows_list)} times in this file."})

        # Post-process Team Sizes
        min_size = HACKATHON_RULES["team_constraints"]["min_size"]
        max_size = HACKATHON_RULES["team_constraints"]["max_size"]
        for team_name, data in teams.items():
            count = len(data["members"])
            if count < min_size or count > max_size:
                for r in data["members"]:
                    errors.append({"row": r, "field": "Team Name", "value": team_name, "code": "INVALID_TEAM_SIZE", "message": f"Team '{team_name}' has {count} members. Must be between {min_size} and {max_size}."})

        # Recalculate valid rows (since post-processing might invalidate some)
        invalid_rows_set = set(e["row"] for e in errors)
        total_rows = len(rows)
        invalid_rows_count = len(invalid_rows_set)
        valid_rows_count = total_rows - invalid_rows_count
        
        # Sort errors by row number
        errors.sort(key=lambda x: x["row"])

        return {
            "success": invalid_rows_count == 0,
            "status": "validation_failed" if invalid_rows_count > 0 else "success",
            "summary": {
                "total_rows": total_rows,
                "valid_rows": valid_rows_count,
                "invalid_rows": invalid_rows_count,
                "warnings": len(warnings)
            },
            "errors": errors,
            "warnings": warnings,
            "normalized_data": rows # We return the original rows because the payment flow needs exact keys matching UI, we just validated them.
        }

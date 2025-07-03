#!/usr/bin/env python3

def fix_syntax(input_file, output_file):
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    in_main_function = False
    has_try_statement = False
    
    for i, line in enumerate(lines):
        # Check if we're entering the main function
        if line.strip() == "def main():":
            in_main_function = True
            fixed_lines.append(line)
            continue
        
        # Check if we're at the try statement in the main function
        if in_main_function and line.strip() == "try:":
            has_try_statement = True
            fixed_lines.append(line)
            continue
        
        # Check if we're at the problematic except statement
        if line.strip() == "except Exception as e:":
            if not has_try_statement:
                # We found an except without a try, so we need to add a try statement
                fixed_lines.append("    try:\n")
                fixed_lines.append(line)
            else:
                fixed_lines.append(line)
            continue
        
        # Add all other lines as is
        fixed_lines.append(line)
    
    with open(output_file, 'w') as f:
        f.writelines(fixed_lines)

if __name__ == "__main__":
    fix_syntax('app.py', 'app_fixed.py')
    print("Syntax fixed. New file saved as app_fixed.py")

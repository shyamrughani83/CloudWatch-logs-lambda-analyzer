#!/usr/bin/env python3

def fix_indentation(input_file, output_file):
    with open(input_file, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    in_problematic_section = False
    
    for line in lines:
        # Check if we're entering a problematic section
        if line.strip().startswith('# Display last fetch time if available') and line.startswith('        '):
            in_problematic_section = True
            fixed_lines.append('    # Display last fetch time if available\n')
            continue
        
        # Fix indentation in problematic section
        if in_problematic_section and line.startswith('        '):
            fixed_lines.append('    ' + line[8:])
        else:
            fixed_lines.append(line)
            in_problematic_section = False
    
    with open(output_file, 'w') as f:
        f.writelines(fixed_lines)

if __name__ == "__main__":
    fix_indentation('app.py', 'app_fixed.py')
    print("Indentation fixed. New file saved as app_fixed.py")

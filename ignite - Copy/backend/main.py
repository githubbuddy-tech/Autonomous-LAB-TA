from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import numpy as np
import hashlib
import json
from datetime import datetime, timedelta
import sqlite3
import os
import subprocess
import tempfile
import re
import difflib

app = FastAPI(
    title="Autonomous Lab TA API",
    version="2.0.0",
    description="Backend API for the Autonomous Lab Teaching Assistant with Manual Upload"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class DebugRequest(BaseModel):
    code: str
    language: str = "python"
    task_id: str
    student_id: str
    hint_level: int = 1

class CodeExecutionRequest(BaseModel):
    code: str
    language: str = "python"

class ManualCheckRequest(BaseModel):
    student_code: str
    manual_code: str
    language: str = "python"
    task_id: str

class UploadManualRequest(BaseModel):
    task_id: str
    language: str = "python"
    manual_code: str
    title: Optional[str] = None
    description: Optional[str] = None

# Database setup
def init_db():
    conn = sqlite3.connect('labta.db')
    cursor = conn.cursor()
    
    # Drop existing tables to recreate with new schema
    cursor.execute('DROP TABLE IF EXISTS debug_sessions')
    cursor.execute('DROP TABLE IF EXISTS lab_tasks')
    cursor.execute('DROP TABLE IF EXISTS hints')
    cursor.execute('DROP TABLE IF EXISTS manual_checks')
    
    # Create analytics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS debug_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT,
            task_id TEXT,
            language TEXT,
            error_type TEXT,
            success BOOLEAN,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            hint_level INTEGER
        )
    ''')
    
    # Create tasks table with all columns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lab_tasks (
            id TEXT PRIMARY KEY,
            title TEXT,
            description TEXT,
            language TEXT,
            difficulty TEXT,
            starter_code TEXT,
            solution_code TEXT,
            manual_code TEXT,
            uploaded_by TEXT DEFAULT 'system',
            upload_time DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create hints table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_type TEXT,
            language TEXT,
            hint_level INTEGER,
            hint_text TEXT
        )
    ''')
    
    # Create manual checks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS manual_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT,
            student_id TEXT,
            similarity_score REAL,
            errors_found INTEGER,
            grade TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Insert sample data
    insert_sample_data()

def insert_sample_data():
    conn = sqlite3.connect('labta.db')
    cursor = conn.cursor()
    
    # Insert sample tasks with manual solutions
    sample_tasks = [
        (
            "python_sum_list",
            "Sum List Function",
            "Write a function that sums all numbers in a list",
            "python",
            "beginner",
            '''def sum_list(numbers):
    # TODO: Implement this function
    pass

# Test the function
print(sum_list([1, 2, 3]))  # Should output 6''',
            '''def sum_list(numbers):
    total = 0
    for num in numbers:
        total += num
    return total

print(sum_list([1, 2, 3]))''',
            '''# Correct manual solution for summing a list
def sum_list(numbers):
    """
    Returns the sum of all numbers in the list.
    
    Args:
        numbers: List of integers or floats
        
    Returns:
        Sum of all numbers in the list
    """
    total = 0
    for number in numbers:
        total += number
    return total

# Test cases
if __name__ == "__main__":
    # Test case 1: Basic test
    test1 = [1, 2, 3, 4, 5]
    result1 = sum_list(test1)
    print(f"Test 1: {test1} -> {result1} (Expected: 15)")
    
    # Test case 2: Empty list
    test2 = []
    result2 = sum_list(test2)
    print(f"Test 2: {test2} -> {result2} (Expected: 0)")
    
    # Test case 3: Negative numbers
    test3 = [-1, 2, -3, 4, -5]
    result3 = sum_list(test3)
    print(f"Test 3: {test3} -> {result3} (Expected: -3)")
    
    # Test case 4: Single element
    test4 = [42]
    result4 = sum_list(test4)
    print(f"Test 4: {test4} -> {result4} (Expected: 42)")
    '''
        ),
        (
            "python_factorial",
            "Factorial Function",
            "Write a recursive function to calculate factorial",
            "python",
            "intermediate",
            '''def factorial(n):
    # TODO: Implement factorial
    pass

print(factorial(5))  # Should output 120''',
            '''def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

print(factorial(5))''',
            '''# Correct manual solution for factorial
def factorial(n):
    """
    Calculate the factorial of a non-negative integer.
    
    Args:
        n: Non-negative integer
        
    Returns:
        Factorial of n
        
    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    if n <= 1:
        return 1
    return n * factorial(n - 1)

def factorial_iterative(n):
    """
    Iterative version of factorial.
    """
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

# Test cases
if __name__ == "__main__":
    test_cases = [0, 1, 5, 7]
    for test in test_cases:
        recursive_result = factorial(test)
        iterative_result = factorial_iterative(test)
        print(f"Factorial({test}) = {recursive_result} (Recursive)")
        print(f"Factorial({test}) = {iterative_result} (Iterative)")
        print(f"Match: {recursive_result == iterative_result}")
        print("-" * 30)
    '''
        ),
        (
            "python_palindrome",
            "Palindrome Checker",
            "Write a function to check if a string is a palindrome",
            "python",
            "beginner",
            '''def is_palindrome(s):
    # TODO: Implement palindrome check
    pass

print(is_palindrome("racecar"))  # Should output True''',
            '''def is_palindrome(s):
    return s == s[::-1]

print(is_palindrome("racecar"))''',
            '''# Correct manual solution for palindrome check
def is_palindrome(s):
    """
    Check if a string is a palindrome (reads the same forwards and backwards).
    
    Args:
        s: String to check
        
    Returns:
        True if palindrome, False otherwise
    """
    # Clean the string: remove spaces and convert to lowercase
    s_clean = ''.join(char.lower() for char in s if char.isalnum())
    
    # Method 1: Compare with reverse
    return s_clean == s_clean[::-1]

def is_palindrome_two_pointers(s):
    """
    Alternative method using two pointers.
    """
    s_clean = ''.join(char.lower() for char in s if char.isalnum())
    left, right = 0, len(s_clean) - 1
    
    while left < right:
        if s_clean[left] != s_clean[right]:
            return False
        left += 1
        right -= 1
    return True

# Test cases
if __name__ == "__main__":
    test_cases = [
        "racecar",
        "hello",
        "A man a plan a canal Panama",
        "12321",
        "12345"
    ]
    
    for test in test_cases:
        result1 = is_palindrome(test)
        result2 = is_palindrome_two_pointers(test)
        print(f"'{test}':")
        print(f"  Method 1 (reverse): {result1}")
        print(f"  Method 2 (two pointers): {result2}")
        print(f"  Both methods agree: {result1 == result2}")
        print()
    '''
        )
    ]
    
    cursor.executemany('''
        INSERT INTO lab_tasks (id, title, description, language, difficulty, starter_code, solution_code, manual_code, uploaded_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'system')
    ''', sample_tasks)
    
    # Insert sample hints
    sample_hints = [
        ("IndexError", "python", 1, "Check your array indices. Python lists are 0-indexed."),
        ("IndexError", "python", 2, "You're trying to access index {index} but the list only has {length} elements."),
        ("IndexError", "python", 3, "Remember: Python lists start at index 0. The last element is at index len(list)-1."),
        ("IndexError", "python", 4, "Try changing 'range(1, len(numbers)+1)' to 'range(len(numbers))' or 'range(0, len(numbers))'."),
        ("SyntaxError", "python", 1, "Check for missing colons, parentheses, or quotes."),
        ("NameError", "python", 1, "A variable or function name is not defined."),
        ("TypeError", "python", 1, "Check if you're using the correct data types."),
        ("off_by_one", "all", 1, "Check your loop boundaries - you might be off by one."),
        ("missing_return", "all", 1, "Your function needs to return a value."),
        ("infinite_loop", "all", 1, "Your loop might run forever. Check your exit condition.")
    ]
    
    cursor.executemany('''
        INSERT INTO hints (error_type, language, hint_level, hint_text)
        VALUES (?, ?, ?, ?)
    ''', sample_hints)
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Helper functions (keep all your existing helper functions here)
def execute_python_code(code: str, timeout: int = 5) -> Dict[str, Any]:
    """Execute Python code safely"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        # Execute with timeout
        result = subprocess.run(
            ['python', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Clean up
        os.unlink(temp_file)
        
        # Determine error type
        error_type = None
        if result.returncode != 0:
            error_type = classify_error(result.stderr)
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
            "error_type": error_type,
            "return_code": result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Execution timed out after {timeout} seconds",
            "error_type": "TimeoutError",
            "output": ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "ExecutionError",
            "output": ""
        }

def execute_javascript_code(code: str, timeout: int = 5) -> Dict[str, Any]:
    """Execute JavaScript code"""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        # Execute with timeout
        result = subprocess.run(
            ['node', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Clean up
        os.unlink(temp_file)
        
        error_type = None
        if result.returncode != 0:
            error_type = classify_error(result.stderr)
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
            "error_type": error_type
        }
        
    except FileNotFoundError:
        return {
            "success": False,
            "error": "Node.js is not installed. Please install Node.js to run JavaScript code.",
            "error_type": "RuntimeMissing",
            "output": ""
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Execution timed out after {timeout} seconds",
            "error_type": "TimeoutError",
            "output": ""
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "ExecutionError",
            "output": ""
        }

def classify_error(error_message: str) -> str:
    """Classify error type from error message"""
    if not error_message:
        return "UnknownError"
    
    error_lower = error_message.lower()
    
    if "indexerror" in error_lower or "arrayindexoutofbounds" in error_lower:
        return "IndexError"
    elif "syntaxerror" in error_lower:
        return "SyntaxError"
    elif "nameerror" in error_lower or "cannot find symbol" in error_lower:
        return "NameError"
    elif "typeerror" in error_lower:
        return "TypeError"
    elif "indentationerror" in error_lower:
        return "IndentationError"
    elif "zerodivisionerror" in error_lower or "divide by zero" in error_lower:
        return "ZeroDivisionError"
    elif "keyerror" in error_lower:
        return "KeyError"
    elif "attributeerror" in error_lower:
        return "AttributeError"
    elif "valueerror" in error_lower:
        return "ValueError"
    elif "timeout" in error_lower:
        return "TimeoutError"
    elif "off by one" in error_lower or "index" in error_lower and "range" in error_lower:
        return "off_by_one"
    elif "missing return" in error_lower or "does not return" in error_lower:
        return "missing_return"
    elif "infinite loop" in error_lower or "while true" in error_lower:
        return "infinite_loop"
    else:
        lines = error_message.strip().split('\n')
        if lines:
            first_line = lines[0]
            if ':' in first_line:
                return first_line.split(':')[0]
        return "RuntimeError"

def get_hint(error_type: str, language: str, hint_level: int = 1) -> str:
    """Get hint from database based on error type and level"""
    conn = sqlite3.connect('labta.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT hint_text FROM hints 
        WHERE error_type = ? AND language = ? AND hint_level = ?
    ''', (error_type, language, hint_level))
    
    result = cursor.fetchone()
    
    if not result:
        cursor.execute('''
            SELECT hint_text FROM hints 
            WHERE error_type = ? AND language = 'all' AND hint_level = ?
        ''', (error_type, hint_level))
        result = cursor.fetchone()
    
    if not result:
        cursor.execute('''
            SELECT hint_text FROM hints 
            WHERE error_type = ? AND (language = ? OR language = 'all')
            ORDER BY hint_level DESC LIMIT 1
        ''', (error_type, language))
        result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return result[0]
    else:
        default_hints = {
            1: f"Error type: {error_type}. Review your code for common mistakes.",
            2: f"The error '{error_type}' occurred. Check your logic and variable usage.",
            3: f"Detailed analysis: The '{error_type}' suggests a problem with your implementation approach.",
            4: f"Let me help you fix this '{error_type}'. Try this approach: "
        }
        return default_hints.get(hint_level, "Review your code and try again.")

def analyze_code_issues(code: str, language: str, execution_result: Dict) -> List[str]:
    """Analyze code for common issues"""
    issues = []
    
    if language == "python":
        if "pass" in code and "def " in code:
            issues.append("Function contains 'pass' and may not be fully implemented")
        
        if "range(1," in code and "len(" in code:
            issues.append("Potential off-by-one error in range() call")
        
        lines = code.split('\n')
        has_print = any("print(" in line for line in lines)
        has_return = any("return " in line for line in lines)
        
        if has_print and not has_return and "def " in code:
            issues.append("Using print() instead of return in function")
        
        if "while True:" in code and "break" not in code:
            issues.append("Potential infinite loop (no break statement)")
    
    if execution_result.get("error_type") == "IndexError":
        issues.append("Index out of bounds - check your array/list indices")
    
    return issues

def generate_suggestions(execution_result: Dict, language: str) -> List[str]:
    """Generate improvement suggestions"""
    suggestions = []
    
    if not execution_result.get("success", False):
        suggestions.append("Fix the error before proceeding")
    
    suggestions.append("Add comments to explain your code")
    
    if language == "python":
        suggestions.append("Consider edge cases (empty list, negative numbers)")
        suggestions.append("Write test cases for your function")
        suggestions.append("Check Python documentation for built-in functions")
    
    return suggestions

def log_debug_session(student_id: str, task_id: str, language: str, 
                     error_type: str, success: bool, hint_level: int):
    """Log debug session to database"""
    conn = sqlite3.connect('labta.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO debug_sessions (student_id, task_id, language, error_type, success, hint_level)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (student_id, task_id, language, error_type, success, hint_level))
    
    conn.commit()
    conn.close()

# Manual Code Checker Class
class ManualCodeChecker:
    """Compare student code with manual/correct code"""
    
    def compare(self, student_code: str, manual_code: str, language: str) -> Dict[str, Any]:
        """Compare student code with manual solution"""
        try:
            # Execute both codes to compare outputs
            student_exec = execute_python_code(student_code) if language == "python" else {"success": False, "output": ""}
            manual_exec = execute_python_code(manual_code) if language == "python" else {"success": False, "output": ""}
            
            results = {
                "syntax_match": self._check_syntax_match(student_code, manual_code),
                "structure_match": self._check_structure_match(student_code, manual_code),
                "logic_match": self._check_logic_match(student_code, manual_code, language),
                "output_match": self._compare_outputs(student_exec.get("output", ""), manual_exec.get("output", "")),
                "errors": self._find_errors(student_code, manual_code, language),
                "similarity_score": self._calculate_similarity_score(student_code, manual_code),
                "code_differences": self._find_code_differences(student_code, manual_code),
                "student_execution": student_exec,
                "manual_execution": manual_exec,
                "suggestions": [],
                "grade": "F"
            }
            
            # Calculate overall score
            scores = [
                results["syntax_match"] * 0.25,
                results["structure_match"] * 0.25,
                results["logic_match"] * 0.25,
                results["output_match"] * 0.25
            ]
            
            overall_score = sum(scores)
            results["overall_score"] = round(overall_score, 2)
            results["grade"] = self._calculate_grade(overall_score)
            
            # Generate suggestions
            results["suggestions"] = self._generate_suggestions(results, student_code, manual_code)
            
            return results
            
        except Exception as e:
            return {"error": f"Manual comparison failed: {str(e)}"}
    
    def _check_syntax_match(self, code1: str, code2: str) -> float:
        """Check syntax similarity"""
        code1_norm = self._normalize_code(code1)
        code2_norm = self._normalize_code(code2)
        
        tokens1 = re.findall(r'\b\w+\b', code1_norm)
        tokens2 = re.findall(r'\b\w+\b', code2_norm)
        
        if not tokens1 or not tokens2:
            return 0.0
        
        set1 = set(tokens1)
        set2 = set(tokens2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _check_structure_match(self, code1: str, code2: str) -> float:
        """Check structural similarity"""
        # Count structural elements
        elements = ["def ", "if ", "for ", "while ", "return ", "import ", "from ", "class "]
        
        count1 = sum(1 for elem in elements if elem in code1)
        count2 = sum(1 for elem in elements if elem in code2)
        
        if count1 == 0 and count2 == 0:
            return 1.0
        
        diff = abs(count1 - count2)
        max_count = max(count1, count2, 1)
        
        return 1.0 - (diff / max_count)
    
    def _check_logic_match(self, student_code: str, manual_code: str, language: str) -> float:
        """Check logical similarity"""
        logic_indicators = {
            "python": ["def ", "return ", "for ", "while ", "if ", "else ", "elif ", "in ", "range(", "len("],
            "javascript": ["function ", "return ", "for ", "while ", "if ", "else ", "const ", "let ", "var "],
            "java": ["public ", "private ", "return ", "for ", "while ", "if ", "else ", "class ", "void "]
        }
        
        indicators = logic_indicators.get(language, [])
        score = 0.0
        
        for indicator in indicators:
            in_student = indicator in student_code
            in_manual = indicator in manual_code
            
            if in_student and in_manual:
                score += 0.1
            elif (in_student and not in_manual) or (not in_student and in_manual):
                score += 0.05
        
        return min(score, 1.0)
    
    def _compare_outputs(self, output1: str, output2: str) -> float:
        """Compare execution outputs"""
        if not output1 or not output2:
            return 0.0
        
        # Normalize outputs
        output1_clean = output1.strip().lower()
        output2_clean = output2.strip().lower()
        
        if output1_clean == output2_clean:
            return 1.0
        
        # Try to extract numeric values
        nums1 = re.findall(r'\d+\.?\d*', output1_clean)
        nums2 = re.findall(r'\d+\.?\d*', output2_clean)
        
        if nums1 and nums2 and nums1 == nums2:
            return 0.8
        
        # Use sequence matcher for partial match
        similarity = difflib.SequenceMatcher(None, output1_clean, output2_clean).ratio()
        return similarity
    
    def _find_errors(self, student_code: str, manual_code: str, language: str) -> List[str]:
        """Find specific errors in student code"""
        errors = []
        
        # Check for pass statement
        if "pass" in student_code and "def " in student_code and "pass" not in manual_code:
            errors.append("Function not implemented (using 'pass')")
        
        # Check for function definition
        if "def " in manual_code and "def " not in student_code:
            errors.append("Missing function definition")
        
        # Check for return statement
        if "return " in manual_code and "return " not in student_code:
            errors.append("Missing return statement")
        
        # Check for proper variable naming
        if language == "python":
            student_vars = re.findall(r'\b([a-z_][a-z0-9_]*)\b', student_code.lower())
            manual_vars = re.findall(r'\b([a-z_][a-z0-9_]*)\b', manual_code.lower())
            
            # Check for single-letter variables (might indicate poor naming)
            single_letter_vars = [var for var in student_vars if len(var) == 1 and var not in ['i', 'j', 'k', 'x', 'y', 'z']]
            if single_letter_vars:
                errors.append(f"Poor variable naming: {', '.join(single_letter_vars)}")
        
        # Check for off-by-one errors
        if "range(1," in student_code and "range(0," in manual_code:
            errors.append("Potential off-by-one error in range")
        
        return errors
    
    def _calculate_similarity_score(self, code1: str, code2: str) -> float:
        """Calculate overall similarity score"""
        # Use difflib for sequence matching
        similarity = difflib.SequenceMatcher(None, code1, code2).ratio()
        return round(similarity, 2)
    
    def _find_code_differences(self, code1: str, code2: str) -> List[Dict[str, Any]]:
        """Find line-by-line differences"""
        lines1 = code1.split('\n')
        lines2 = code2.split('\n')
        
        differences = []
        max_lines = max(len(lines1), len(lines2))
        
        for i in range(max_lines):
            line1 = lines1[i] if i < len(lines1) else ""
            line2 = lines2[i] if i < len(lines2) else ""
            
            if line1 != line2:
                differences.append({
                    "line": i + 1,
                    "student": line1,
                    "manual": line2,
                    "type": "different" if line1 and line2 else "missing" if not line1 else "extra"
                })
        
        return differences[:20]
    
    def _normalize_code(self, code: str) -> str:
        """Normalize code for comparison"""
        # Remove comments
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
        # Remove extra whitespace
        code = re.sub(r'\s+', ' ', code)
        # Remove strings for better tokenization
        code = re.sub(r'"[^"]*"', '""', code)
        code = re.sub(r"'[^']*'", "''", code)
        return code.strip().lower()
    
    def _calculate_grade(self, score: float) -> str:
        """Convert score to letter grade"""
        if score >= 0.9:
            return "A"
        elif score >= 0.8:
            return "B"
        elif score >= 0.7:
            return "C"
        elif score >= 0.6:
            return "D"
        else:
            return "F"
    
    def _generate_suggestions(self, results: Dict, student_code: str, manual_code: str) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        if results["output_match"] < 0.5:
            suggestions.append("Focus on getting the correct output first")
        
        if results["syntax_match"] < 0.7:
            suggestions.append("Review basic syntax and structure")
        
        if results["logic_match"] < 0.6:
            suggestions.append("Work on understanding the logic flow")
        
        if results["errors"]:
            suggestions.append(f"Fix the identified errors: {', '.join(results['errors'][:3])}")
        
        if "pass" in student_code and "def " in student_code:
            suggestions.append("Replace 'pass' with actual implementation")
        
        if len(student_code) < len(manual_code) * 0.5:
            suggestions.append("Your solution might be too simple. Check if you're missing important parts")
        
        return suggestions

# Initialize manual checker
manual_checker = ManualCodeChecker()

# API Endpoints
@app.get("/")
async def root():
    return {
        "message": "Autonomous Lab TA API with Manual Upload",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "/labs": "Get all lab tasks",
            "/labs/{id}": "Get specific lab task",
            "/debug": "Debug code and get hints",
            "/execute": "Execute code",
            "/manual-check": "Compare with manual solution",
            "/upload-manual": "Upload manual solution",
            "/user-manuals": "Get user uploaded manuals",
            "/manual/{id}": "Delete manual",
            "/health": "Health check",
            "/analytics/common-errors": "Get analytics"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "language_runtimes": {
            "python": True,
            "javascript": is_runtime_available("node"),
            "java": is_runtime_available("javac")
        }
    }

def is_runtime_available(command: str) -> bool:
    """Check if a runtime command is available"""
    try:
        subprocess.run([command, "--version"], capture_output=True, check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

@app.get("/labs")
async def get_all_labs():
    """Get all available lab tasks"""
    conn = sqlite3.connect('labta.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, description, language, difficulty, uploaded_by
        FROM lab_tasks 
        ORDER BY 
            CASE WHEN uploaded_by = 'system' THEN 0 ELSE 1 END,
            language, difficulty
    ''')
    
    labs = []
    for row in cursor.fetchall():
        labs.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "language": row[3],
            "difficulty": row[4],
            "uploaded_by": row[5],
            "is_custom": row[5] != "system"
        })
    
    conn.close()
    
    return {"labs": labs}

@app.get("/labs/{task_id}")
async def get_lab_task(task_id: str):
    """Get specific lab task with starter code"""
    conn = sqlite3.connect('labta.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, title, description, language, difficulty, starter_code, solution_code, manual_code, uploaded_by
        FROM lab_tasks WHERE id = ?
    ''', (task_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task": {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "language": row[3],
            "difficulty": row[4],
            "starter_code": row[5],
            "solution_code": row[6],
            "manual_code": row[7],
            "uploaded_by": row[8],
            "is_custom": row[8] != "system"
        }
    }

@app.post("/debug")
async def debug_code(request: DebugRequest):
    """Debug code and get hints"""
    try:
        execution_result = {}
        if request.language == "python":
            execution_result = execute_python_code(request.code)
        elif request.language == "javascript":
            execution_result = execute_javascript_code(request.code)
        else:
            return {
                "success": False,
                "error": f"Language {request.language} not supported yet",
                "error_type": "UnsupportedLanguage",
                "output": "",
                "hint": f"{request.language} support is coming soon!"
            }
        
        error_type = execution_result.get("error_type", "UnknownError")
        hint = get_hint(error_type, request.language, request.hint_level)
        
        issues = analyze_code_issues(request.code, request.language, execution_result)
        suggestions = generate_suggestions(execution_result, request.language)
        
        log_debug_session(
            student_id=request.student_id,
            task_id=request.task_id,
            language=request.language,
            error_type=error_type,
            success=execution_result.get("success", False),
            hint_level=request.hint_level
        )
        
        return {
            "success": execution_result.get("success", False),
            "output": execution_result.get("output", ""),
            "error": execution_result.get("error", ""),
            "error_type": error_type,
            "hint": hint,
            "hint_level": request.hint_level,
            "issues": issues,
            "suggestions": suggestions,
            "task_id": request.task_id,
            "language": request.language
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")

@app.post("/execute")
async def execute_code(request: CodeExecutionRequest):
    """Execute code without debugging"""
    try:
        if request.language == "python":
            result = execute_python_code(request.code)
        elif request.language == "javascript":
            result = execute_javascript_code(request.code)
        else:
            return {
                "success": False,
                "error": f"Language {request.language} not supported yet",
                "output": ""
            }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Execution error: {str(e)}")

@app.post("/manual-check")
async def manual_check_code(request: ManualCheckRequest):
    """Compare student code with manual solution"""
    try:
        if not request.manual_code.strip():
            return {"error": "Manual code is required for comparison"}
        
        result = manual_checker.compare(
            request.student_code,
            request.manual_code,
            request.language
        )
        
        # Log the manual check
        if "error" not in result:
            conn = sqlite3.connect('labta.db')
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO manual_checks (task_id, student_id, similarity_score, errors_found, grade)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                request.task_id,
                f"manual_check_{hashlib.md5(request.student_code.encode()).hexdigest()[:8]}",
                result.get("similarity_score", 0),
                len(result.get("errors", [])),
                result.get("grade", "F")
            ))
            
            conn.commit()
            conn.close()
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manual check error: {str(e)}")

@app.post("/upload-manual")
async def upload_manual_solution(request: UploadManualRequest):
    """Upload a manual solution"""
    try:
        if not request.manual_code.strip():
            raise HTTPException(status_code=400, detail="Manual code cannot be empty")
        
        if not request.task_id.strip():
            raise HTTPException(status_code=400, detail="Task ID cannot be empty")
        
        conn = sqlite3.connect('labta.db')
        cursor = conn.cursor()
        
        # Check if task exists
        cursor.execute('SELECT id FROM lab_tasks WHERE id = ?', (request.task_id,))
        existing_task = cursor.fetchone()
        
        if existing_task:
            # Update existing task
            cursor.execute('''
                UPDATE lab_tasks 
                SET manual_code = ?, language = ?, title = COALESCE(?, title),
                    description = COALESCE(?, description), uploaded_by = 'user'
                WHERE id = ?
            ''', (request.manual_code, request.language, request.title, request.description, request.task_id))
        else:
            # Create new task
            task_title = request.title or f"Custom Task - {request.task_id}"
            task_description = request.description or "Custom manual solution uploaded by user"
            
            cursor.execute('''
                INSERT INTO lab_tasks (id, title, description, language, difficulty, starter_code, solution_code, manual_code, uploaded_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'user')
            ''', (
                request.task_id,
                task_title,
                task_description,
                request.language,
                "custom",
                "# Add your starter code here",
                "# Add your solution code here",
                request.manual_code
            ))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Manual solution uploaded for task '{request.task_id}'",
            "task_id": request.task_id,
            "title": task_title if 'task_title' in locals() else request.title,
            "language": request.language,
            "code_length": len(request.manual_code),
            "code_preview": request.manual_code[:200] + ("..." if len(request.manual_code) > 200 else "")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload error: {str(e)}")

@app.get("/user-manuals")
async def get_user_manuals():
    """Get all user-uploaded manual solutions"""
    try:
        conn = sqlite3.connect('labta.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, title, description, language, manual_code, upload_time
            FROM lab_tasks 
            WHERE uploaded_by = 'user'
            ORDER BY upload_time DESC
        ''')
        
        manuals = []
        for row in cursor.fetchall():
            manuals.append({
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "language": row[3],
                "code_preview": row[4][:200] + ("..." if len(row[4]) > 200 else ""),
                "full_code": row[4],
                "uploaded_at": row[5],
                "code_length": len(row[4])
            })
        
        conn.close()
        
        return {"manuals": manuals}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching manuals: {str(e)}")

@app.delete("/manual/{task_id}")
async def delete_manual(task_id: str):
    """Delete a manual solution"""
    try:
        conn = sqlite3.connect('labta.db')
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM lab_tasks WHERE id = ? AND uploaded_by = ?', (task_id, "user"))
        
        if cursor.rowcount == 0:
            conn.close()
            raise HTTPException(status_code=404, detail="Manual not found or cannot be deleted (only user uploads can be deleted)")
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": f"Manual '{task_id}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")

@app.get("/analytics/common-errors")
async def get_common_errors(days: int = 7):
    """Get analytics about common errors"""
    conn = sqlite3.connect('labta.db')
    cursor = conn.cursor()
    
    threshold_date = datetime.now() - timedelta(days=days)
    
    cursor.execute('''
        SELECT error_type, COUNT(*) as count 
        FROM debug_sessions 
        WHERE timestamp >= ? AND error_type IS NOT NULL
        GROUP BY error_type 
        ORDER BY count DESC
        LIMIT 10
    ''', (threshold_date.isoformat(),))
    
    error_distribution = []
    for row in cursor.fetchall():
        error_distribution.append({
            "error_type": row[0],
            "count": row[1]
        })
    
    cursor.execute('''
        SELECT 
            SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes,
            COUNT(*) as total
        FROM debug_sessions 
        WHERE timestamp >= ?
    ''', (threshold_date.isoformat(),))
    
    row = cursor.fetchone()
    success_rate = row[0] / row[1] if row[1] > 0 else 0
    
    cursor.execute('''
        SELECT language, COUNT(*) as count 
        FROM debug_sessions 
        WHERE timestamp >= ?
        GROUP BY language 
        ORDER BY count DESC
    ''', (threshold_date.isoformat(),))
    
    language_distribution = []
    for row in cursor.fetchall():
        language_distribution.append({
            "language": row[0],
            "count": row[1]
        })
    
    cursor.execute('SELECT COUNT(*) FROM debug_sessions WHERE timestamp >= ?', 
                   (threshold_date.isoformat(),))
    total_interactions = cursor.fetchone()[0]
    
    # Get manual check statistics
    cursor.execute('''
        SELECT grade, COUNT(*) as count 
        FROM manual_checks 
        WHERE timestamp >= ?
        GROUP BY grade 
        ORDER BY grade
    ''', (threshold_date.isoformat(),))
    
    manual_grades = {}
    for row in cursor.fetchall():
        manual_grades[row[0]] = row[1]
    
    # Get user uploads count
    cursor.execute('SELECT COUNT(*) FROM lab_tasks WHERE uploaded_by = "user" AND upload_time >= ?',
                   (threshold_date.isoformat(),))
    user_uploads = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "error_distribution": error_distribution,
        "success_rate": success_rate,
        "language_distribution": language_distribution,
        "total_interactions": total_interactions,
        "manual_check_grades": manual_grades,
        "user_uploads_count": user_uploads,
        "period_days": days
    }

# Run the application
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("🚀 Autonomous Lab TA Backend with Manual Upload")
    print("=" * 70)
    print("📊 Database initialized with sample data")
    print("📝 Manual upload and comparison enabled")
    print("📤 User manuals storage ready")
    print("🌐 API ready at http://localhost:8000")
    print("📚 Documentation: http://localhost:8000/docs")
    print("=" * 70)
    
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)